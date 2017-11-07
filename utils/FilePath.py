__author__ = 'B.Ankhbold'
# -*- coding: utf-8

from PyQt4.QtCore import *
from DatabaseUtils import *
import os

class FilePath(object):

    @staticmethod
    def view_file_path():

        archive_app_path = r'D:/TM_LM2/archive/view.pdf'
        if not os.path.exists(archive_app_path):
            os.makedirs(archive_app_path)

        return str(archive_app_path)

    @staticmethod
    def view_file_png_path():

        archive_app_path = r'D:/TM_LM2/archive/view.png'
        if not os.path.exists(archive_app_path):
            os.makedirs(archive_app_path)

        return str(archive_app_path)

    @staticmethod
    def ub_archive_path():

        working_aimag = DatabaseUtils.working_l1_code()
        working_soum = DatabaseUtils.working_l2_code()
        host = QSettings().value(SettingsConstants.HOST, "")
        dest_dir = 'documents'

        if host == "localhost":
            ub_archive_path = r'D:/TM_LM2/archive/' + working_aimag + '/' + working_soum + '/ub_archive'
            if not os.path.exists(ub_archive_path):
                os.makedirs(ub_archive_path)
            return str(ub_archive_path)
        else:
            # if host[-2:] != '14':
            # dest_dir = 'archive'
            share_path = ''.join(['\\\\', host, '\\', dest_dir.replace(':', '$')])
            ub_archive_path = share_path + '\\' + working_aimag + '\\' + working_soum + '\\ub_archive'
            if not os.path.exists(ub_archive_path):
                os.makedirs(ub_archive_path)
            return str(ub_archive_path)

    @staticmethod
    def app_file_path():

        working_aimag = DatabaseUtils.working_l1_code()
        working_soum = DatabaseUtils.working_l2_code()
        host = QSettings().value(SettingsConstants.HOST, "")
        dest_dir = 'documents'

        if host == "localhost":
            archive_app_path = r'D:/TM_LM2/archive/'+working_aimag+'/'+working_soum+'/application'
            if not os.path.exists(archive_app_path):
                os.makedirs(archive_app_path)
            return str(archive_app_path)
        else:
            # if host[-2:] != '14':
            # dest_dir = 'archive'
            share_path = ''.join(['\\\\', host, '\\', dest_dir.replace(':', '$')])
            archive_app_path = share_path + '\\' + working_aimag+'\\'+working_soum+'\\application'
            if not os.path.exists(archive_app_path):
                os.makedirs(archive_app_path)
            return str(archive_app_path)

    @staticmethod
    def cert_file_path():

        working_aimag = DatabaseUtils.working_l1_code()
        working_soum = DatabaseUtils.working_l2_code()
        host = QSettings().value(SettingsConstants.HOST, "")
        dest_dir = 'documents'

        if host == "localhost":
            archive_cert_path = r'D:/TM_LM2/archive/'+working_aimag+'/'+working_soum+'/certificate'
            if not os.path.exists(archive_cert_path):
                os.makedirs(archive_cert_path)
            return str(archive_cert_path)
        else:
            # if host[-2:] != '14':
            # dest_dir = 'archive'
            share_path = ''.join(['\\\\', host, '\\', dest_dir.replace(':', '$')])
            archive_cert_path = share_path + '\\' + working_aimag+'\\'+working_soum+'\\certificate'
            if not os.path.exists(archive_cert_path):
                os.makedirs(archive_cert_path)
            return str(archive_cert_path)

    @staticmethod
    def contrac_file_path():

        working_aimag = DatabaseUtils.working_l1_code()
        working_soum = DatabaseUtils.working_l2_code()
        host = QSettings().value(SettingsConstants.HOST, "")
        dest_dir = 'documents'

        if host == "localhost":
            archive_contract_path = r'D:/TM_LM2/archive/'+working_aimag+'/'+working_soum+'/contract'
            if not os.path.exists(archive_contract_path):
                os.makedirs(archive_contract_path)
            return str(archive_contract_path)
        else:
            share_path = ''.join(['\\\\', host, '\\', dest_dir.replace(':', '$')])
            archive_contract_path = share_path + '\\' + working_aimag+'\\'+working_soum+'\\contract'
            if not os.path.exists(archive_contract_path):
                os.makedirs(archive_contract_path)
            return str(archive_contract_path)

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
            # if host[-2:] != '14':
            # dest_dir = 'archive'
            share_path = ''.join(['\\\\', host, '\\', dest_dir.replace(':', '$')])
            archive_decision_path = share_path + '\\' + working_aimag+'\\'+working_soum+'\\decision'
            if not os.path.exists(archive_decision_path):
                os.makedirs(archive_decision_path)
            return str(archive_decision_path)

    @staticmethod
    def equipment_file_path():

        working_aimag = DatabaseUtils.working_l1_code()
        working_soum = DatabaseUtils.working_l2_code()
        host = QSettings().value(SettingsConstants.HOST, "")
        dest_dir = 'documents'

        if host == "localhost":
            archive_equipment_path = r'D:/TM_LM2/archive/'+working_aimag+'/'+working_soum+'/equipment'
            if not os.path.exists(archive_equipment_path):
                os.makedirs(archive_equipment_path)
            return str(archive_equipment_path)
        else:
            # if host[-2:] != '14':
            # dest_dir = 'archive'
            share_path = ''.join(['\\\\', host, '\\', dest_dir.replace(':', '$')])
            archive_equipment_path = share_path + '\\' + working_aimag+'\\'+working_soum+'\\equipment'
            if not os.path.exists(archive_equipment_path):
                os.makedirs(archive_equipment_path)
            return str(archive_equipment_path)

    @staticmethod
    def feetaxzone_file_path():

        working_aimag = DatabaseUtils.working_l1_code()
        working_soum = DatabaseUtils.working_l2_code()
        host = QSettings().value(SettingsConstants.HOST, "")
        dest_dir = 'documents'

        if host == "localhost":
            archive_feetaxzone_path = r'D:/TM_LM2/archive/'+working_aimag+'/'+working_soum+'/feetaxzone'
            if not os.path.exists(archive_feetaxzone_path):
                os.makedirs(archive_feetaxzone_path)
            return str(archive_feetaxzone_path)
        else:
            # if host[-2:] != '14':
            # dest_dir = 'archive'
            share_path = ''.join(['\\\\', host, '\\', dest_dir.replace(':', '$')])
            archive_feetaxzone_path = share_path + '\\' + working_aimag+'\\'+working_soum+'\\feetaxzone'
            print archive_feetaxzone_path
            if not os.path.exists(archive_feetaxzone_path):
                os.makedirs(archive_feetaxzone_path)
            return str(archive_feetaxzone_path)

    @staticmethod
    def legaldocuments_file_path():

        working_aimag = DatabaseUtils.working_l1_code()
        working_soum = DatabaseUtils.working_l2_code()
        host = QSettings().value(SettingsConstants.HOST, "")
        dest_dir = 'documents'

        if host == "localhost":
            archive_legaldocuments_path = r'D:/TM_LM2/archive/'+working_aimag+'/'+working_soum+'/legaldocuments'
            if not os.path.exists(archive_legaldocuments_path):
                os.makedirs(archive_legaldocuments_path)
            return str(archive_legaldocuments_path)
        else:
            share_path = ''.join(['\\\\', host, '\\', dest_dir.replace(':', '$')])
            archive_legaldocuments_path = share_path + '\\' + working_aimag+'\\'+working_soum+'\\legaldocuments'
            if not os.path.exists(archive_legaldocuments_path):
                os.makedirs(archive_legaldocuments_path)
            return str(archive_legaldocuments_path)

    @staticmethod
    def ownership_file_path():

        working_aimag = DatabaseUtils.working_l1_code()
        working_soum = DatabaseUtils.working_l2_code()
        host = QSettings().value(SettingsConstants.HOST, "")
        dest_dir = 'documents'

        if host == "localhost":
            archive_ownership_path = r'D:/TM_LM2/archive/'+working_aimag+'/'+working_soum+'/ownership'
            if not os.path.exists(archive_ownership_path):
                os.makedirs(archive_ownership_path)
            return str(archive_ownership_path)
        else:
            share_path = ''.join(['\\\\', host, '\\', dest_dir.replace(':', '$')])
            archive_ownership_path = share_path + '\\' + working_aimag+'\\'+working_soum+'\\ownership'
            if not os.path.exists(archive_ownership_path):
                os.makedirs(archive_ownership_path)
            return str(archive_ownership_path)