__author__ = 'B.Ankhbold'
# -*- coding: utf-8

from PyQt4.QtCore import *
from DatabaseUtils import *
import os

class PasturePath(object):
    
    @staticmethod
    def view_file_path():

        archive_app_path = r'D:/TM_LM2/archive/view.pdf'
        if not os.path.exists(archive_app_path):
            os.makedirs(archive_app_path)

        return str(archive_app_path)

    @staticmethod
    def view_photo_path():

        archive_app_path = r'D:/TM_LM2/pasture/view.jpg'
        if not os.path.exists(archive_app_path):
            os.makedirs(archive_app_path)

        return str(archive_app_path)

    @staticmethod
    def app_file_path():

        host = QSettings().value(SettingsConstants.HOST, "")
        dest_dir = 'documents'

        if host == "localhost":
            archive_app_path = r'D:/TM_LM2/pasture/applications'
            if not os.path.exists(archive_app_path):
                os.makedirs(archive_app_path)
            return str(archive_app_path)
        else:
            share_path = ''.join(['\\\\', host, '\\', dest_dir.replace(':', '$')])
            archive_app_path = share_path + '\\pasture\\applications'
            if not os.path.exists(archive_app_path):
                os.makedirs(archive_app_path)
            return str(archive_app_path)

    @staticmethod
    def contrac_file_path():

        host = QSettings().value(SettingsConstants.HOST, "")
        dest_dir = 'documents'

        if host == "localhost":
            archive_contract_path = r'D:/TM_LM2/pasture/contracts'
            if not os.path.exists(archive_contract_path):
                os.makedirs(archive_contract_path)
            return str(archive_contract_path)
        else:
            share_path = ''.join(['\\\\', host, '\\', dest_dir.replace(':', '$')])
            archive_contract_path = share_path +'\\pasture\\contracts'
            if not os.path.exists(archive_contract_path):
                os.makedirs(archive_contract_path)
            return str(archive_contract_path)

    @staticmethod
    def pasture_photo_file_path():

        host = QSettings().value(SettingsConstants.HOST, "")
        dest_dir = 'documents'

        if host == "localhost":
            pasture_point_path = r'D:/TM_LM2/pasture/point'
            if not os.path.exists(pasture_point_path):
                os.makedirs(pasture_point_path)
            return str(pasture_point_path)
        else:
            share_path = ''.join(['\\\\', host, '\\', dest_dir.replace(':', '$')])
            pasture_point_path = share_path + '\\pasture\\point'
            if not os.path.exists(pasture_point_path):
                os.makedirs(pasture_point_path)
            return str(pasture_point_path)

    @staticmethod
    def decision_file_path():

        working_aimag = DatabaseUtils.working_l1_code()
        working_soum = DatabaseUtils.working_l2_code()
        host = QSettings().value(SettingsConstants.HOST, "")
        dest_dir = 'documents'

        if host == "localhost":
            archive_decision_path = r'D:/TM_LM2/archive/'+working_aimag+'/'+working_soum+'/decision'
            if not os.path.exists(archive_decision_path):
                os.makedirs(archive_decision_path)
            return str(archive_decision_path)
        else:
            share_path = ''.join(['\\\\', host, '\\', dest_dir.replace(':', '$')])
            archive_decision_path = share_path + '\\' + working_aimag+'\\'+working_soum+'\\decision'
            if not os.path.exists(archive_decision_path):
                os.makedirs(archive_decision_path)
            return str(archive_decision_path)