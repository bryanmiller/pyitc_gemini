#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ITC_selenium import *
import logging
import sys
import time

# Convenience definitions for GMOS
# https://www.gemini.edu/instrumentation/gmos/components#Gratings
gmos_dispersers = {'GMOSN': {'B1200': 'B1200_G5301',
                             'R831': 'R831_G5302',
                             'B600': 'B600_G5303',
                             'R400': 'R400_G5305',
                             'R150': 'R150_G5306',
                             'Imaging': 'MIRROR'
                             },
                   'GMOSS': {'B1200': 'B1200_G5321',
                             'R831': 'R831_G5322',
                             'B600': 'B600_G5323',
                             'R400': 'R400_G5325',
                             'R150': 'R150_G5326',
                             'Imaging': 'MIRROR'
                             }
                   }

# not complete
# https://www.gemini.edu/instrumentation/gmos/components#Filters
gmos_filters = {'GMOSN': {'None': 'NONE',
                          'g': 'g_G0301',
                          'r': 'r_G0303',
                          'i': 'i_G0302',
                          'z': 'z_G0304',
                          'Z': 'Z_G0322',
                          'Y': 'Y_G0323',
                          'ri': 'ri_G0349',
                          'GG455': 'GG455_G0305',
                          'OG515': 'OG515_G0306',
                          'RG610': 'OG515_G0307'
                          },
                'GMOSS': {'None': 'NONE',
                          'u': 'u_G0332',
                          'g': 'g_G0325',
                          'r': 'r_G0326',
                          'i': 'i_G0327',
                          'z': 'z_G0328',
                          'Z': 'Z_G0343',
                          'Y': 'Y_G0344',
                          'GG455': 'GG455_G0329',
                          'OG515': 'OG515_G0330',
                          'RG610': 'OG515_G0331',
                          'RG780': 'OG515_G0334'
                          },
                }

# Should be complete
gmos_slits = {'None': 'FPU_NONE',
         'IFU-2': 'IFU_1',
         'IFU-LB': 'IFU_2',
         'IFU-RR': 'IFU_3',
         '0.25arcsec': 'LONGSLIT_1',
         '0.5arcsec': 'LONGSLIT_2',
         '0.75arcsec': 'LONGSLIT_3',
         '1.0arcsec': 'LONGSLIT_4',
         '1.5arcsec': 'LONGSLIT_5',
         '2.0arcsec': 'LONGSLIT_6',
         '5.0arcsec': 'LONGSLIT_7',
         }


def main():

    logger = SetLog('GMOSS')

    Testing = ParseArgs(sys.argv)

    Test1(Testing)
    Test2(Testing)
    Test3(Testing)
    Test5(Testing)
    Test6(Testing)


#-----------------------------------------------------------------------

def Test1(Testing):
    # GMOSS longslit, QSO

    logger = logging.getLogger()

    Instrument = "GMOSS"
    logger.info('Running %s Test 1/5', Instrument)
    URL = GetURL(Instrument, Testing, site='web')

    RecordURL(URL, Instrument, Testing)

    driver = startWebpage(URL, headless=True)

    #Select Point Source with brightness 22 mag
    setPointSource(driver, 22, "MAG")
    setBrightnessNormalization(driver, "R")

    #Select LibrarySpectrum of non stellar object QSO
    setLibrarySpectrumNonStellar(driver, "QSO")

    #Set Optical Properties
    setOpticalPropertiesGMOS(driver, gmos_dispersers[Instrument]["R400"],
                             gmos_filters[Instrument]["OG515"], 750, gmos_slits["1.0arcsec"])

    #Set Detector Properties (CCD, ybin (spatial), xbin (spectral), coating, WFS)
    setDetectorPropertiesGMOSS(driver, "ham", 2, 4, "Silver", "OIWFS")

    #Set Observing Conditions (IQ, CC, WV, SB, airmass)
    setObservingConditions(driver, 70, 50, 100, 50, 1.5)

    #Set Calculation Method (nexp, exptime, frac on source)
    setCalculationMethod(driver,"ratio", 2, 1200, 1.0)

    #Set Analysis Method
    setAnalysisMethodGMOS(driver, "optimum", 5)

    #press Calculate
    calculate(driver)
    time.sleep(4)

    #Save output to a file(s)
    extractData(driver,"Spectroscopy", "1", Instrument, Testing)

    #Quit driver
    driver.quit()


# -----------------------------------------------------------------------

def Test2(Testing):
    # GMOSS imaging, uniform surface brightness

    logger = logging.getLogger()

    Instrument = "GMOSS"
    logger.info('Running %s Test 2/5', Instrument)
    URL = GetURL(Instrument, Testing, site='web')

    driver = startWebpage(URL)

    # Select Extended Source, Uniform Brightness 17 mag/sq arcsec at R
    setUniformSource(driver, 17, "MAG_PSA")
    setBrightnessNormalization(driver, "R")

    # Select Power Law Spectrum with index -1.0
    setPowerLawSpectrum(driver, -1.0)

    # Set Optical Properties
    # setOpticalPropertiesGMOS(driver, "MIRROR", "z_G0328", 0, "FPU_NONE")
    setOpticalPropertiesGMOS(driver, gmos_dispersers[Instrument]["Imaging"],
                             gmos_filters[Instrument]["z"], 0, gmos_slits["None"])

    # Set Detector Properties (CCD, ybin (spatial), xbin (spectral), coating, WFS)
    setDetectorPropertiesGMOSS(driver, "ham", 2, 2, "Silver", "OIWFS")

    # Set Observing Conditions (IQ, CC, WV, SB, airmass)
    setObservingConditions(driver, 70, 50, 100, 80, 1.5)

    # Set Calculation Method (method, nexp, exptime, frac on source)
    setCalculationMethod(driver, "ratio", 5, 150, 1.0)

    # Set Analysis Method
    setAnalysisMethodGMOS(driver, "optimum", 5)

    # press Calculate
    calculate(driver)
    time.sleep(4)

    # Save output to a file(s)
    extractData(driver, "imaging", "2", Instrument, Testing)

    # Quit driver
    driver.quit()


# -----------------------------------------------------------------------

def Test3(Testing):
    # GMOSS imaging, G2V

    logger = logging.getLogger()

    Instrument = "GMOSS"
    logger.info('Running %s Test 3/5', Instrument)
    URL = GetURL(Instrument, Testing, site='web')

    driver = startWebpage(URL)

    # Select Point Source with brightness 22 mag
    setPointSource(driver, 22, "MAG")
    setBrightnessNormalization(driver, "R")

    #Select Library Spectrum star of type G2
    setLibrarySpectrum(driver,"G2V")

    # Set Optical Properties
    # setOpticalPropertiesGMOS(driver, "MIRROR", "z_G0328", 0, "FPU_NONE")
    setOpticalPropertiesGMOS(driver, gmos_dispersers[Instrument]["Imaging"],
                             gmos_filters[Instrument]["z"], 0, gmos_slits["None"])

    # Set Detector Properties (CCD, ybin (spatial), xbin (spectral), coating, WFS)
    setDetectorPropertiesGMOSS(driver, "ham", 2, 2, "Silver", "OIWFS")

    # Set Observing Conditions (IQ, CC, WV, SB, airmass)
    setObservingConditions(driver, 70, 50, 100, 80, 1.5)

    # Set Calculation Method (method, nexp, exptime, frac on source)
    setCalculationMethod(driver, "ratio", 5, 150, 1.0)

    # Set Analysis Method
    setAnalysisMethodGMOS(driver, "optimum", 5)

    # press Calculate
    calculate(driver)
    time.sleep(4)

    # Save output to a file(s)
    extractData(driver, "imaging", "3", Instrument, Testing)

    # Quit driver
    driver.quit()


#-----------------------------------------------------------------------

def Test5(Testing):
    # GMOSS longslit, emission line

    logger = logging.getLogger()

    Instrument = "GMOSS"
    logger.info('Running %s Test 5/5', Instrument)
    URL = GetURL(Instrument, Testing, site='web')

    driver = startWebpage(URL)

    # Select Point Source 17 mag at B
    setPointSource(driver, 17, "MAG")
    setBrightnessNormalization(driver, "R")

    # Select Emission Line
    setEmissionLine(driver, "0.656", "5.0e-17", "ergs_flux", "500.0", "1.0e-17", "ergs_fd_wavelength")

    # Set Optical Properties
    # setOpticalPropertiesGMOS(driver, "B1200_G5321", "i_G0327", 650, "LONGSLIT_5")
    setOpticalPropertiesGMOS(driver, gmos_dispersers[Instrument]["B1200"],
                             gmos_filters[Instrument]["i"], 650, gmos_slits["1.5arcsec"])

    # Set Detector Properties (CCD, ybin (spatial), xbin (spectral), coating, WFS)
    setDetectorPropertiesGMOSS(driver, "ham", 4, 4, "Silver", "PWFS")

    # Set Observing Conditions (IQ, CC, WV, SB, airmass)
    setObservingConditions(driver, 100, 80, 100, 100, 1.5)

    # Set Calculation Method (method, nexp, exptime, frac on source)
    setCalculationMethod(driver, "ratio", 2, 120, 1.0)

    # Set Analysis Method
    setAnalysisMethodGMOS(driver, "optimum", 5)

    # press Calculate
    calculate(driver)
    time.sleep(4)

    # Save output to a file(s)
    extractData(driver, "Spectroscopy", "5", Instrument, Testing)

    # Quit driver
    driver.quit()


# -----------------------------------------------------------------------

def Test6(Testing):
    # GSAOI - H-band
    logger = logging.getLogger()

    Instrument = "GSAOI"
    logger.info('Running %s Test 6...', Instrument)
    URL = GetURL(Instrument, Testing, site='web')

    driver = startWebpage(URL)

    # Select Point Source 21 mag at K
    setPointSource(driver, 21, "MAG")
    setBrightnessNormalization(driver, "K")

    # Select Library Spectrum of type K4V
    setLibrarySpectrum(driver, "K4V")

    # Set Optical Properties (filter)
    setOpticalPropertiesGSAOI(driver, "H")

    # Set Detector Properties (readmode, coating, Strehl% , Strehl band)
    setDetectorPropertiesGSAOI(driver, "faint", "Silver", "15", "H")

    # Set Observing Conditions (IQ, CC, WV, SB, airmass)
    setObservingConditions(driver, 85, 50, 100, 100, 1.5)

    # Set Calculation Method (method, nexp, ncoadd, exptime, frac on source)
    # Need to include coadds
    setCalculationMethodCoadd(driver, "ratio", 30, 3, 60, 1.0)

    # Set Analysis Method (method, offset, largeSkyOffset, aperDiam)
    setAnalysisMethodGSAOI(driver, "optimum", Offset=5.0, largeSkyOffset=0)

    # press Calculate
    calculate(driver)
    time.sleep(4)

    # Save output to a file(s)
    extractData(driver, "Imaging", "6", Instrument, Testing)

    # Quit driver
    driver.quit()

# -----------------------------------------------------------------------


if __name__ == "__main__":
    main()

#-----------------------------------------------------------------------
