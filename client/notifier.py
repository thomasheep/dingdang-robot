# -*- coding: utf-8-*-
import Queue
import atexit
from plugins import Email
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import db
import config
from app_utils import wechatUser
import tushare as ts
class Notifier(object):

    class NotificationClient(object):

        def __init__(self, gather, timestamp):
            self.gather = gather
            self.timestamp = timestamp

        def run(self):
            self.timestamp = self.gather(self.timestamp)

    def __init__(self, profile, brain):
        self._logger = logging.getLogger(__name__)
        self.q = Queue.Queue()
        self.profile = profile
        self.notifiers = []
        self.brain = brain

        if 'email' in profile and \
           ('enable' not in profile['email'] or profile['email']['enable']):
            self.notifiers.append(self.NotificationClient(
                self.handleEmailNotifications, None))
        else:
            self._logger.warning('email account not set ' +
                                 'in profile, email notifier will not be used')

        sched = BackgroundScheduler(daemon=True)
        sched.start()
        sched.add_job(self.gather, 'interval', seconds=30)
        atexit.register(lambda: sched.shutdown(wait=False))

    def gather(self):
        [client.run() for client in self.notifiers]
        self.get_stock_notify()

    def get_stock_notify(self):
        wxbot = config.get_uni_obj("wxbot")
        if not wxbot:
            return
        watch_list = db.get_instance().get_notify_list()
        c_list = watch_list['codelist']
        self._logger.info("watch:%s",str(c_list).decode('string_escape'))
        if c_list:
            m_list = watch_list['lastmodifylist']
            msg_list = []
            df = ts.get_realtime_quotes(c_list)
            sendFlag = False
            for index, row in df.iterrows():
                
                modi_time = row['date']+' '+row['time']
                if index==0:
                    msg_list.append(' '+str(index +1)+": ")
                else:
                    msg_list.append(str(index +1)+": ")
                msg_list.append(row['code'])                    
                msg_list.append(row['name'])
                msg_list.append(row['price'])
                msg_list.append(row['time'])
                msg_list.append('\n')
                if modi_time != m_list[index]:
                    sendFlag = True
                    db.get_instance().update_notify(row['code'], modi_time)
            if sendFlag:
                msg = ' '.join(msg_list)
                wechatUser(config.profile, wxbot, '股价关注', msg)


    def handleEmailNotifications(self, lastDate):
        """Places new email notifications in the Notifier's queue."""
        emails = Email.fetchUnreadEmails(self.profile, since=lastDate)
        if emails:
            lastDate = Email.getMostRecentDate(emails)

        def styleEmail(e):
            subject = Email.getSubject(e, self.profile)
            if Email.isEchoEmail(e, self.profile):
                if Email.isNewEmail(e):
                    return subject.replace('[echo]', '')
                else:
                    return ""
            elif Email.isControlEmail(e, self.profile):
                self.brain.query([subject.replace('[control]', '')
                                  .strip()], None, True)
                return ""
            sender = Email.getSender(e)
            return "您有来自 %s 的新邮件 %s" % (sender, subject)
        for e in emails:
            self.q.put(styleEmail(e))

        return lastDate

    def getNotification(self):
        """Returns a notification. Note that this function is consuming."""
        try:
            notif = self.q.get(block=False)
            return notif
        except Queue.Empty:
            return None

    def getAllNotifications(self):
        """
            Return a list of notifications in chronological order.
            Note that this function is consuming, so consecutive calls
            will yield different results.
        """
        notifs = []

        notif = self.getNotification()
        while notif:
            notifs.append(notif)
            notif = self.getNotification()

        return notifs
