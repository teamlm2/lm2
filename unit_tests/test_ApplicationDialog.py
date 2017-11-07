__author__ = 'anna'

import unittest
from PyQt4.QtTest import QTest
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QDialog, QApplication
from qgis.core import *
import sys

from trunk.controller.ApplicationsDialog import ApplicationsDialog
from trunk.utils.PluginUtils import PluginUtils
from trunk.utils.SessionHandler import SessionHandler


class test_ApplicationDialog(unittest.TestCase):

    def setUp(self):

        self.app = QApplication(sys.argv)
        user = "anna"
        password = "anna"
        database = "darkhan_2808"
        host = "localhost"
        port = "5432"

        SessionHandler().create_session(user, password, host, port, database)
        self.session = SessionHandler().session_instance()

        #self.app = QgsApplication.setPrefixPath("/usr/local", True)
        #QgsApplication.initQgis()
        #if len(QgsProviderRegistry.instance().providerList()) == 0:
        #    raise RuntimeError('No data providers available.')

        #QgsApplication.exitQgis()

        application = CtApplication()
        self.application_dialog = ApplicationsDialog(application, self.navigator, False)

    def test_defaults(self):
        try:
            ok_button = self.application_dialog.apply_button
            QTest.mouseClick(ok_button, Qt.LeftButton)

            cancel_button = self.application_dialog.close_button
            QTest.mouseClick(cancel_button, Qt.LeftButton)

        except:
            self.assertRaises(ValueError)

if __name__ == '__main__':
    unittest.main()
