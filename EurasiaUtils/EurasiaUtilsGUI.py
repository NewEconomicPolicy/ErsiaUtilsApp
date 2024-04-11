# -------------------------------------------------------------------------------
# Name:
# Purpose:     GUI create DailyDayCent input files
# Author:      Mike Martin
# Created:     16/12/2015
# Licence:     <your licence>
# -------------------------------------------------------------------------------
# !/usr/bin/env python

__prog__ = 'EurasiaUtilsGUI.py'
__version__ = '0.0.1'
__author__ = 's03mm5'

import sys

from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (QLabel, QWidget, QApplication, QHBoxLayout, QVBoxLayout, QGridLayout, QPushButton,
                             QFileDialog)
from pyodbc import connect, drivers
from os.path import join, isdir, isfile, split, splitext, exists, basename, splitdrive
from os import getcwd, walk, chdir
from filecmp import cmp as cmpr_two_files

from hwsd_bil import HWSD_bil
from eurasia_funcs import _generate_country_shape_files, _create_codes_table
from excel_to_netcdf_funcs import convert_excel_file, convert_csv_file
from initialise_funcs import initiation, write_config_file

ERROR_STR = '*** Error *** '

class Form(QWidget):
    """
    X
    """

    def __init__(self, parent=None):
        """

        """
        super(Form, self).__init__(parent)

        self.version = 'EurasiaUtilsGUI'
        initiation(self)

        # define two vertical boxes, in LH vertical box put the painter and in RH put the grid
        # define horizon box to put LH and RH vertical boxes in
        hbox = QHBoxLayout()
        hbox.setSpacing(10)

        # left hand vertical box consists of png image
        # ============================================
        lh_vbox = QVBoxLayout()

        # LH vertical box contains image only
        lbl20 = QLabel()
        pixmap = QPixmap(self.settings['fname_png'])
        lbl20.setPixmap(pixmap)

        lh_vbox.addWidget(lbl20)

        # add LH vertical box to horizontal box
        hbox.addLayout(lh_vbox)

        # right hand box consists of combo boxes, labels and buttons
        # ==========================================================
        rh_vbox = QVBoxLayout()

        # The layout is done with the QGridLayout
        grid = QGridLayout()
        grid.setSpacing(10)  # set spacing between widgets

        irow = 1

        # line 7 - option to select run file
        # ==================================
        w_excel_file = QPushButton("Excel file")
        helpText = 'Excel file consisting of global ID, latitude, longitude, landuse type, soil type, ' \
                   + 'country code and country'
        w_excel_file.setToolTip(helpText)
        grid.addWidget(w_excel_file, irow, 0)
        w_excel_file.clicked.connect(self.fetchExcelFile)

        w_lbl05 = QLabel()
        grid.addWidget(w_lbl05, irow, 1, 1, 6)
        self.w_lbl05 = w_lbl05

        # line 7 - option to select run file
        # ==================================
        irow += 1
        use_run_file = QPushButton("Run file")
        helpText = 'CSV run file consisting of global ID, latitude, longitude, landuse type, soil type, ' \
                   + 'country code and country'
        use_run_file.setToolTip(helpText)

        grid.addWidget(use_run_file, irow, 0)
        use_run_file.clicked.connect(self.fetchRunFile)

        w_lbl07 = QLabel(self.settings['run_fname'])
        grid.addWidget(w_lbl07, irow, 1, 1, 6)
        self.w_lbl07 = w_lbl07

        # =======
        irow += 1
        w_cnvrt_excel = QPushButton("Convert Excel")
        helpText = 'Convert Padraig Excel file to CSV'
        w_cnvrt_excel.setToolTip(helpText)
        w_cnvrt_excel.setEnabled(False)
        grid.addWidget(w_cnvrt_excel, irow, 0)
        w_cnvrt_excel.clicked.connect(self.convertExcelClicked)

        w_create_file = QPushButton("Unpack country shapes")
        helpText = 'Read zipped shape files of countries and, using first 3 letters of file name, assign country ' \
                   'names using ISO 3166-1 alpha-3 code table'
        w_create_file.setToolTip(helpText)
        grid.addWidget(w_create_file, irow, 1)
        w_create_file.clicked.connect(self.createFilesClicked)

        w_codes = QPushButton('Write country names & codes')
        helpText = 'Read Daycent run file and extract Code_CindyPotsdam and CountryName fields then write these to a ' \
                   'CSV file comprising country names and codes'
        w_codes.setToolTip(helpText)
        # w_codes.setEnabled(False)
        grid.addWidget(w_codes, irow, 2)
        w_codes.clicked.connect(self.codesClicked)

        w_exit = QPushButton("Exit", self)
        grid.addWidget(w_exit, irow, 3)
        w_exit.clicked.connect(self.exitClicked)

        # =======
        irow += 1
        w_cnvrt_csv = QPushButton("Convert CSV")
        helpText = 'Convert Padraig CSV file to NetCDF4'
        w_cnvrt_csv.setToolTip(helpText)
        # w_cnvrt_csv.setEnabled(False)
        grid.addWidget(w_cnvrt_csv, irow, 0)
        w_cnvrt_csv.clicked.connect(self.convertCsvClicked)

        # =======
        irow += 1
        w_hwsdv1 = QPushButton("Test V1 Access")
        helpText = 'Test HWSD V1 Access'
        w_hwsdv1.setToolTip(helpText)
        grid.addWidget(w_hwsdv1, irow, 0)
        w_hwsdv1.clicked.connect(self.testHwsdV1Clicked)

        # =======
        irow += 1
        w_pyodbc = QPushButton("Test V2 Access")
        helpText = 'Test HWSD V2 Access'
        w_pyodbc.setToolTip(helpText)
        grid.addWidget(w_pyodbc, irow, 0)
        w_pyodbc.clicked.connect(self.testAccessClicked)

        # =======
        irow += 1
        w_cmpr_mngmt = QPushButton("Compare mngmt ")
        helpText = 'Compare management.txt files'
        w_cmpr_mngmt.setToolTip(helpText)
        w_cmpr_mngmt.setEnabled(False)
        grid.addWidget(w_cmpr_mngmt, irow, 0)
        w_cmpr_mngmt.clicked.connect(self.cmprMngmtClicked)

        # add grid to RH vertical box
        rh_vbox.addLayout(grid)

        # vertical box goes into horizontal box
        hbox.addLayout(rh_vbox)

        # the horizontal box fits inside the window
        self.setLayout(hbox)

        # posx, posy, width, height
        self.setGeometry(300, 300, 300, 250)
        self.setWindowTitle(self.version + ' - unpack shape files')

        # set values from last run
        # ========================
        self.w_lbl05.setText(self.settings['excel_fname'])
        self.w_lbl07.setText(self.settings['run_fname'])

    def testHwsdV1Clicked(self):
        """

        """
        lat, lon = (28.1, 74.23)
        hwsd = HWSD_bil(self.lggr, self.settings['hwsd_dir'])
        nvals_read = hwsd.read_bbox_mu_globals([lon, lat], snglPntFlag=True)
        mu_globals = hwsd.get_mu_globals_dict()
        if mu_globals is None:
            print('No soil records for this area\n')
            return

        # create and instantiate a new class NB this stanza enables single site
        # ==================================
        hwsd_mu_globals = type('test', (), {})()
        hwsd_mu_globals.soil_recs = hwsd.get_soil_recs(mu_globals)
        if len(mu_globals) == 0:
            print('No soil data for this area\n')
            return

        mu_globals_props = {next(iter(mu_globals)): 1.0}

        mess = 'Retrieved {} values  of HWSD grid consisting of {} rows and {} columns: ' \
               '\n\tnumber of unique mu_globals: {}'.format(nvals_read, hwsd.nlats, hwsd.nlons, len(mu_globals))
        print(mess)

        return

    def cmprMngmtClicked(self):
        """

        """
        access_db_fn = 'E:\\Apps\\test_db\\Database1.accdb'
        sims_dir = 'G:\\GlblEcssOutputs\\EcosseSims\\Africa_Wheat_Africa_Wheat08A1B'

        MAX_CMPRSNS = 100000000
        ic = 0
        n_oks = 0
        for directory, subdirs_raw, files in walk(sims_dir):
            fn_g = join(directory, 'management.txt')
            if isfile(fn_g):
                drv, file_name = splitdrive(fn_g)
            else:
                print(fn_g + ' does not exist')
                continue

            fn_z = join('Z:', file_name)
            if cmpr_two_files(fn_g, fn_z):
                n_oks + 1
                if ic == 100 * (int(ic / 100)):
                    print('OK: ' + directory)
            else:
                print('differ: ' + '\n\t' + fn_g + '\n\t' + fn_z)

            if ic > MAX_CMPRSNS:
                # print(directory)
                break

            ic += 1

        print('OK: ' + directory)

    def testAccessClicked(self):
        """

        """
        access_db_fn = 'E:\\Apps\\test_db\\Database1.accdb'
        access_db_fn = 'E:\\HWSD_V2\\mdb\\HWSD2.mdb'
        lat, lon = (28.1, 74.23)

        ms_srch_str = 'Microsoft Access Driver'
        drvr_nms = [drvr_nm for drvr_nm in drivers() if drvr_nm.startswith(ms_srch_str)]
        if len(drvr_nms) == 0:
            print(ERROR_STR + 'could not find ' + ms_srch_str + ' among ODBC drivers')
            return
        ms_drvr = drvr_nms[0]

        conn = connect(Driver=ms_drvr, DBQ=access_db_fn)
        cursor = conn.cursor()

        for table_info in cursor.tables(tableType='TABLE'):
            print(table_info.table_name)

        # retcode = cursor.execute('select * from D_ROOTS')

        for row in cursor.columns(table='HWSD2_LAYERS'):
            print(row.column_name)

        retcode = cursor.execute('select * from HWSD2_LAYERS where HWSD2_SMU_ID = 9612')
        for rec in cursor.fetchall():
            print(rec)

        cursor.close()

        return

    def convertExcelClicked(self):
        """
        C
        """
        convert_excel_file(self)

    def convertCsvClicked(self):
        """
        C
        """
        convert_csv_file(self)

    def fetchExcelFile(self):
        """
        allow user to select Excel file
        """
        fname = self.w_lbl05.text()
        if fname == "":
            fname = self.settings['root_dir']

        fname = QFileDialog.getOpenFileName(self, 'Open run file', fname, 'Excel files (*.xlsx)')

        self.w_lbl05.setText(fname[0])

    def fetchRunFile(self):
        """
        # We pop up the QtGui.QFileDialog. The first string in the getOpenFileName()
        # method is the caption. The second string specifies the dialog working directory.
        # By default, the file filter is set to All files (*).
        """
        fname = self.w_lbl07.text()
        if fname == "":
            fname = self.settings['root_dir']

        fname = QFileDialog.getOpenFileName(self, 'Open run file', fname, 'csv files (*.csv)')

        self.w_lbl07.setText(fname)

    def codesClicked(self):
        """
        C
        """
        _create_codes_table(self)

    def createFilesClicked(self):
        """
        C
        """

        _generate_country_shape_files(self)

    def exitClicked(self):
        """
        write last GUI selections and close logger
        """
        write_config_file(self)

        try:
            self.lggr.handlers[0].close()  # close logging
        except AttributeError:
            pass
        self.close()

def main():
    """
    C
    """
    app = QApplication(sys.argv)  # create QApplication object
    form = Form()  # instantiate form
    # display the GUI and start the event loop if we're not running batch mode
    form.show()  # paint form
    sys.exit(app.exec_())  # start event loop


if __name__ == '__main__':
    main()
