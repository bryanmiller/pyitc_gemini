#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
#import difflib
import datetime
import logging
import os
from selenium import webdriver
# from selenium.webdriver.firefox.options import Options
# from selenium import selenium
# from selenium.common.exceptions import TimeoutException
# from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
import sys
# import subprocess
import time
if sys.version_info.major == 2:
    from urllib2 import urlopen
    reload(sys)
    sys.setdefaultencoding('utf8')
elif sys.version_info.major == 3:
    from urllib.request import urlopen

# 2014 Mar 10 - Reorganize output, astephens
# 2014 Mar 12 - Ignore URLs (lines with "http") when performing diff
# 2014 Mar 14 - Add CompareDirs
# 2015 Feb  2 - AWS, ignore page-break lines between multiple plots
# 2021 Feb 12 - BWM, code cleanup

sleep = 0.1 # May need to increase on fast computers in headless mode


#---------------------------------------------------------------------------------------------------

def Usage():
    print ('')
    print ('SYNOPSIS')
    cmd = sys.argv[0]
    print ('      ', cmd[cmd.rfind('/')+1:], 'test/production')
    print ('')
    print ('DESCRIPTION')
    print ('       Blah.')
    print ('')
    print ('OPTIONS')
    #print ('       -d : debug mode')
    print ('')
    # raise SystemExit


#---------------------------------------------------------------------------------------------------

def GetURL(Instrument, Testing, site='web'):

    url = ''
    if Testing:
        url = 'http://itcdev.cl.gemini.edu:9080/itc/servlets/web/'
        # url = 'http://sbfitcdev1.cl.gemini.edu:9080/itc/servlets/web/'
    else:
        if site in ['gn', 'gs']:
            # Used by ODBs
            url = 'http://' + site + 'odb.gemini.edu:8442/itc/servlets/web/'
        elif site == 'web':
            # Used by ITC web pages
            url = 'https://www.gemini.edu/itc/servlets/web/'
        else:
            print('Site must be either "gn", "gs", or "web".')
            return url

    if Instrument == 'NIRI':
        url += 'ITCniri.html'
    elif Instrument == 'F2':
        url += 'ITCflamingos2.html'
    elif Instrument == 'GMOSN':
        url += 'ITCgmos.html'
    elif Instrument == 'GMOSS':
        url += 'ITCgmosSouth.html'
    elif Instrument == 'GNIRS':
        url += 'ITCgnirs.html'
    elif Instrument == 'NIFS':
        url += 'ITCnifs.html'
    elif Instrument == 'Michelle':
        url += 'ITCmichelle.html'
    elif Instrument == 'GSAOI':
        url += 'ITCgsaoi.html'
    elif Instrument == 'TReCS':
        url += 'ITCtrecs.html'

    return(url)


#---------------------------------------------------------------------------------------------------
# Get the output path

def GetPath(Instrument, Testing, outdir='/tmp/'):

    # path = os.getenv('HOME') + '/tmp/' + Instrument + '/' + str(datetime.date.today())
    path = os.getenv('HOME') + outdir

    if Testing:
        path += '/Test'
    else:
        path += '/Prod'

    return(path)


#---------------------------------------------------------------------------------------------------

def SetLog(instrument, outdir='/tmp'):

    path = os.environ['HOME'] + outdir + '/'
    logfile = path + '/ITC_' + instrument + '.' + datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S") + '.log'
    logger = ConfigureLogging(logfile)
    #logger = logging.getLogger()
    logger.info('Log = %s', logfile)
    return(logger)


#---------------------------------------------------------------------------------------------------

def ParseArgs(argv):

    logger = logging.getLogger()

    Testing = False

    if len(argv) != 2:
        Usage()
        logger.info('Using default (Production URL...)')
    else:
        if 'test' in argv[1].lower():
            Testing = True
            logger.info('Using Test URL...')
        elif 'prod' in argv[1].lower():
            logger.info('Using Production URL...')
        else:
            Usage()
            raise SystemExit

    return(Testing)


#---------------------------------------------------------------------------------------------------
# Record the URL in the output directory for future reference

def RecordURL(URL, Instrument, Testing):

    path = GetPath(Instrument, Testing)

    if not os.path.exists(path):
        os.mkdir(path)
    
    URLFile = open(path + '/URL','w')
    URLFile.write(URL + '\n')
    URLFile.close()


#---------------------------------------------------------------------------------------------------
# Pass a URL that contains the ITC tests

def startWebpage(URL, headless=True):
    
    # Create a new instance of the Firefox driver
    # https://developer.mozilla.org/en-US/docs/Mozilla/Firefox/Headless_mode
    options = webdriver.firefox.options.Options()
    if headless:
        options.add_argument('-headless')
    driver = webdriver.Firefox(executable_path='geckodriver', options=options)

    # go to the GMOS ITC Page
    driver.get(URL)
    return driver


#---------------------------------------------------------------------------------------------------
# Input:    Brightness
#           Units

def setPointSource(driver, Brightness, Units):
    logger = logging.getLogger('setPointSource')

    #Select Point Source
    driver.find_element_by_xpath("//input[@name='Profile' and @value='POINT']").click()
    
    #Set Point Source Brightness
    if type(Brightness) is float:
        Brightness = str(Brightness)
    logger.debug('Setting Point Source brightness to %s', Brightness)
    driver.find_element_by_name("psSourceNorm").clear()
    driver.find_element_by_name("psSourceNorm").send_keys(Brightness)
    
    #Set Point Source Units
    driver.find_element_by_xpath("//select[@name='psSourceUnits']/option[@value='" + Units + "']").click()


#---------------------------------------------------------------------------------------------------

def setGaussianSource(driver, FullWidth, Brightness, Units):
    logger = logging.getLogger('setGaussianSource')

    # Turn Fullwidth to str
    if type(FullWidth) is float:
        FullWidth = str(FullWidth)
 
 	# Turn Brightness to str
    if type(Brightness) is float:
        Brightness = str(Brightness)
           
    logger.debug('Setting Gaussian source with FWHM = %s and brightness = %s %s', FullWidth, Brightness, Units)

    # Select Gaussian Source
    driver.find_element_by_xpath("//input[@name='Profile' and @value='GAUSSIAN']").click()

    # Set Full Width Half Max
    driver.find_element_by_name("gaussFwhm").clear()
    driver.find_element_by_name("gaussFwhm").send_keys(FullWidth)
    
    # Set Brightness
    driver.find_element_by_name("gaussSourceNorm").clear()
    driver.find_element_by_name("gaussSourceNorm").send_keys(Brightness)
    
    # Set Brightness Units
    driver.find_element_by_xpath("//select[@name='gaussSourceUnits']/option[@value='" + Units + "']").click()


#---------------------------------------------------------------------------------------------------

def setUniformSource(driver, Brightness, Units):
    logger = logging.getLogger('setUniformSource')

    time.sleep(sleep)
    
    if type(Brightness) is float:
        Brightness = str(Brightness)
    
    logger.debug('Setting uniform brightness to %s %s', Brightness, Units)

    # Select Uniform Source
    driver.find_element_by_xpath("//input[@name='Profile' and @value='UNIFORM']").click()
    
    # Set Brightness
    driver.find_element_by_name("usbSourceNorm").clear()
    driver.find_element_by_name("usbSourceNorm").send_keys(Brightness)
    
    # Set Brightness Units
    driver.find_element_by_xpath("//select[@name='usbSourceUnits']/option[@value='" + Units + "']").click()


#---------------------------------------------------------------------------------------------------

def setBrightnessNormalization(driver, Wavelength):
    
    driver.find_element_by_xpath("""//select[@name='WavebandDefinition']/option[@value=""" + '"' + Wavelength + '"' + """]""").click()


#---------------------------------------------------------------------------------------------------

def setLibrarySpectrum(driver, Type):
    
    #Set for Library Spectrum of a star with specific stellar type
    driver.find_element_by_xpath("//input[@value='LIBRARY_STAR' and @name='Distribution']").click()

    #Choose stellar type
    driver.find_element_by_xpath("//select[@name='stSpectrumType']/option[@value='" + Type + "']").click()


#---------------------------------------------------------------------------------------------------

def setLibrarySpectrumNonStellar(driver, Type):
    
    #Set for Library Spectrum of a non-stellar object
    driver.find_element_by_xpath("//input[@value='LIBRARY_NON_STAR' and @name='Distribution']").click()
    
    #Choose non-stellar object
    driver.find_element_by_xpath("//select[@name='nsSpectrumType']/option[@value='" + Type + "']").click()


#---------------------------------------------------------------------------------------------------

def setPowerLawSpectrum(driver, Index):
    logger = logging.getLogger('setPowerLawSpectrum')
   
    time.sleep(sleep)

    if type(Index) is int or type(Index) is float:
        Index = str(Index)

    logger.debug('Setting power law index to %s', Index)

    # Set for Power Law Spectrum
    driver.find_element_by_xpath("//input[@value='PLAW' and @name='Distribution']").click()
    
    # Set Index
    driver.find_element_by_name("powerIndex").clear()
    driver.find_element_by_name("powerIndex").send_keys(Index)


#---------------------------------------------------------------------------------------------------

def setBlackBodySpectrum(driver, Temperature):
    logger = logging.getLogger('setBlackBodySpectrum')
   
    time.sleep(sleep)

    if type(Temperature) is int or type(Temperature) is float:
        Temperature = str(Temperature)

    logger.debug('Setting blackbody temperature to %s deg', Temperature)
    
    # Set for BlackBody
    driver.find_element_by_xpath("//input[@value='BBODY' and @name='Distribution']").click()
    
    # Set Temperature
    driver.find_element_by_name("BBTemp").clear()
    driver.find_element_by_name("BBTemp").send_keys(Temperature)


#---------------------------------------------------------------------------------------------------

def setEmissionLine(driver, Wavelength, LineFlux, LineFluxUnits, LineWidth, FluxDensity, FluxDensityUnits):
    logger = logging.getLogger('setEmissionLine')

    time.sleep(sleep)

    # Choose Emission Line
    driver.find_element_by_xpath("//input[@value='ELINE' and @name='Distribution']").click()
    
    # Set Wavelength
    if type(Wavelength) is float:
        Wavelength = str(Wavelength)
    logger.debug('Setting emission line wavelength to %s um', Wavelength)
    driver.find_element_by_name("lineWavelength").clear()
    driver.find_element_by_name("lineWavelength").send_keys(Wavelength)    
    
    # Set Line Flux
    if type(LineFlux) is float:
        LineFlux = str(LineFlux)
    logger.debug('Setting emission line flux to %s %s', LineFlux, LineFluxUnits)
    driver.find_element_by_name("lineFlux").clear()
    driver.find_element_by_name("lineFlux").send_keys(LineFlux)     
    
    # Set Line Flux Units
    driver.find_element_by_xpath("//select[@name='lineFluxUnits']/option[@value='" + LineFluxUnits + "']")
    
    # Set Line Width
    if type(LineWidth) is float:
        LineWidth = str(LineWidth)
    logger.debug('Setting emission line width to %s', LineWidth)
    driver.find_element_by_name("lineWidth").clear()
    driver.find_element_by_name("lineWidth").send_keys(LineWidth)
    
    # Set Flux Density
    if type(FluxDensity) is float:
        FluxDensity = str(FluxDensity)
    logger.debug('Setting emission line flux density to %s %s', FluxDensity, FluxDensityUnits)
    driver.find_element_by_name("lineContinuum").clear()
    driver.find_element_by_name("lineContinuum").send_keys(FluxDensity)   
    
    # Set Flux Density Units
    driver.find_element_by_xpath("//select[@name='lineContinuumUnits']/option[@value='" + FluxDensityUnits + "']")


#---------------------------------------------------------------------------------------------------
# This is for the OLD GMOS ITC with EEV, Hamamatsu Red and Blue CCDS

def setDetectorPropertiesGMOS(driver, CCD, SpatialBinning, SpectralBinning, Coating, Wavefront):
    
    #Set CCD
    if "eev" in CCD.lower():
        #Set to EEV array
        driver.find_element_by_xpath("//input[@name='DetectorManufacturer' and @value='E2V']").click()
    elif "red" in CCD.lower():
        #Set to Hamamatsu Red
        driver.find_element_by_xpath("//input[@name='DetectorManufacturer' and @value='HAMAMATSU']").click()
    else:
        #Set to Hamamatsu Blue
        driver.find_element_by_xpath("//input[@name='DetectorManufacturer' and @value='HAMAMATSU']").click()
     
    #Set Spatial Binning
    if type(SpatialBinning) is int:
        SpatialBinning = str(SpatialBinning)
    driver.find_element_by_xpath("//input[@name='spatBinning' and @value='" + SpatialBinning + "']").click()
    
    #Set spectral Binning
    if type(SpectralBinning) is int:
        SpectralBinning = str(SpectralBinning)
    driver.find_element_by_xpath("//input[@name='specBinning' and @value='" + SpectralBinning + "']") .click()  
     
    #Set Mirror Coating
    if "silver" in Coating.lower():
        driver.find_element_by_xpath("//input[@value='SILVER' and @name='Coating']").click()
    elif "alum" in Coating.lower():
        driver.find_element_by_xpath("//input[@value='ALUMINIUM' and @name='Coating']").click()
        
    #Set Wavefront Sensor
    if "oiwfs" in Wavefront.lower():
        driver.find_element_by_xpath("//input[@value='OIWFS' and @name='Type']").click()
    elif "pwfs" in Wavefront.lower():
        driver.find_element_by_xpath("//input[@value='PWFS' and @name='Type']").click()


#---------------------------------------------------------------------------------------------------
# Set Detector Properties for GMOS-N

def setDetectorPropertiesGMOSN(driver, CCD, SpatialBinning, SpectralBinning, Coating, Wavefront):

    # Set CCD
    if   "dd"  in CCD.lower():
        driver.find_element_by_xpath("//input[@name='DetectorManufacturer' and @value='E2V']").click()
    elif "leg" in CCD.lower():
        driver.find_element_by_xpath("//input[@name='DetectorManufacturer' and @value='E2V']").click()
    elif "ham" in CCD.lower():
        driver.find_element_by_xpath("//input[@name='DetectorManufacturer' and @value='HAMAMATSU']").click()

    # Set Spatial Binning
    if type(SpatialBinning) is int:
        SpatialBinning = str(SpatialBinning)
    driver.find_element_by_xpath("//input[@name='spatBinning' and @value='" + SpatialBinning + "']").click()
    
    # Set spectral Binning
    if type(SpectralBinning) is int:
        SpectralBinning = str(SpectralBinning)
    driver.find_element_by_xpath("//input[@name='specBinning' and @value='" + SpectralBinning + "']") .click()  
     
    # Set Mirror Coating
    if "silver" in Coating.lower():
        driver.find_element_by_xpath("//input[@value='SILVER' and @name='Coating']").click()
    elif "alum" in Coating.lower():
        driver.find_element_by_xpath("//input[@value='ALUMINIUM' and @name='Coating']").click()
        
    # Set Wavefront Sensor
    if "oiwfs" in Wavefront.lower():
        driver.find_element_by_xpath("//input[@value='OIWFS' and @name='Type']").click()
    elif "pwfs" in Wavefront.lower():
        driver.find_element_by_xpath("//input[@value='PWFS' and @name='Type']").click()


#---------------------------------------------------------------------------------------------------
# Set Detector Properties for GMOS-S

def setDetectorPropertiesGMOSS(driver, CCD, SpatialBinning, SpectralBinning, Coating, Wavefront):

    # Set CCD
    if   "eev" in CCD.lower():
        driver.find_element_by_xpath("//input[@name='DetectorManufacturer' and @value='E2V']").click()
    elif "ham" in CCD.lower():
        driver.find_element_by_xpath("//input[@name='DetectorManufacturer' and @value='HAMAMATSU']").click()

    # Set Spatial Binning
    if type(SpatialBinning) is int:
        SpatialBinning = str(SpatialBinning)
    driver.find_element_by_xpath("//input[@name='spatBinning' and @value='" + SpatialBinning + "']").click()
    
    # Set spectral Binning
    if type(SpectralBinning) is int:
        SpectralBinning = str(SpectralBinning)
    driver.find_element_by_xpath("//input[@name='specBinning' and @value='" + SpectralBinning + "']") .click()
    
    # Set Mirror Coating
    if "silver" in Coating.lower():
        driver.find_element_by_xpath("//input[@value='SILVER' and @name='Coating']").click()
    elif "alum" in Coating.lower():
        driver.find_element_by_xpath("//input[@value='ALUMINIUM' and @name='Coating']").click()
        
    # Set Wavefront Sensor
    if "oiwfs" in Wavefront.lower():
        driver.find_element_by_xpath("//input[@value='OIWFS' and @name='Type']").click()
    elif "pwfs" in Wavefront.lower():
        driver.find_element_by_xpath("//input[@value='PWFS' and @name='Type']").click()


#---------------------------------------------------------------------------------------------------
# Bryan Miller, 2013-09-05

def setDetectorPropertiesGSAOI(driver, Noise, Coating, Strehl, StrehlBand):
    logger = logging.getLogger('setDetectorPropertiesGSAOI')

    # Set Read Noise Level
    if "veryfaint" in Noise.lower():
        driver.find_element_by_xpath("//input[@value='VERY_FAINT' and @name='ReadMode']").click()
    elif "faint" in Noise.lower():
        driver.find_element_by_xpath("//input[@value='FAINT' and @name='ReadMode']").click()
    else:
        driver.find_element_by_xpath("//input[@value='BRIGHT' and @name='ReadMode']").click()    
        
    # Set Mirror Coating
    if "silver" in Coating.lower():
        driver.find_element_by_xpath("//input[@value='SILVER' and @name='Coating']").click()
    elif "alum" in Coating.lower():
        driver.find_element_by_xpath("//input[@value='ALUMINIUM' and @name='Coating']").click()
        
    # Set Strehl
    # if type(Strehl) is int or type(Strehl) is float:
    #         Strehl = str(Strehl)
    #
    # logger.debug('Setting Strehl to %s', Strehl)
    # driver.find_element_by_name("avgStrehl").clear()
    # driver.find_element_by_name("avgStrehl").send_keys(Strehl)
    #
    # # Set Strehl Band
    # driver.find_element_by_xpath("//select[@name='strehlBand']/option[@value='" + StrehlBand + "']").click()


#---------------------------------------------------------------------------------------------------
# Bryan Miller, 2013-09-10

def setDetectorPropertiesF2(driver, Noise, Coating, Port, Wavefront):
    
    #Set Read Noise Level
    if "low" in Noise.lower():
        driver.find_element_by_xpath("//input[@value='FAINT_OBJECT_SPEC' and @name='ReadMode']").click()
    elif "med" in Noise.lower():
        driver.find_element_by_xpath("//input[@value='MEDIUM_OBJECT_SPEC' and @name='ReadMode']").click()
    else:
        driver.find_element_by_xpath("//input[@value='BRIGHT_OBJECT_SPEC' and @name='ReadMode']").click()    
        
    #Set Mirror Coating
    if "silver" in Coating.lower():
        driver.find_element_by_xpath("//input[@value='SILVER' and @name='Coating']").click()
    elif "alum" in Coating.lower():
        driver.find_element_by_xpath("//input[@value='ALUMINIUM' and @name='Coating']").click()
        
    #Set Port
    if "side" in Port.lower():
        driver.find_element_by_xpath("//input[@value='SIDE_LOOKING' and @name='IssPort']").click()
    elif "up" in Port.lower():
        driver.find_element_by_xpath("//input[@value='UP_LOOKING' and @name='IssPort']").click()

    #Set Wavefront Sensor
    if "oiwfs" in Wavefront.lower():
        driver.find_element_by_xpath("//input[@value='OIWFS' and @name='Type']").click()
    elif "pwfs" in Wavefront.lower():
        driver.find_element_by_xpath("//input[@value='PWFS' and @name='Type']").click()


#---------------------------------------------------------------------------------------------------

def setDetectorPropertiesNIRI(driver, Bias, Noise, Coating, Wavefront):
    
    #Set Detector Bias
    if "low" in Bias.lower():
        driver.find_element_by_xpath("//input[@value='SHALLOW' and @name='WellDepth']").click()
    else:
        driver.find_element_by_xpath("//input[@value='DEEP' and @name='WellDepth']").click()

    #Set Read Noise Level
    if "low" in Bias.lower():
        driver.find_element_by_xpath("//input[@value='IMAG_SPEC_NB' and @name='ReadMode']").click()
    elif "med" in Bias.lower():
        driver.find_element_by_xpath("//input[@value='IMAG_1TO25' and @name='ReadMode']").click()
    else:
        driver.find_element_by_xpath("//input[@value='IMAG_SPEC_3TO5' and @name='ReadMode']").click()    
        
    #Set Mirror Coating
    if "silver" in Coating.lower():
        driver.find_element_by_xpath("//input[@value='SILVER' and @name='Coating']").click()
    elif "alum" in Coating.lower():
        driver.find_element_by_xpath("//input[@value='ALUMINIUM' and @name='Coating']").click()
        
    #Set Wavefront Sensor
    if "oiwfs" in Wavefront.lower():
        driver.find_element_by_xpath("//input[@value='OIWFS' and @name='Type']").click()
    elif "pwfs" in Wavefront.lower():
        driver.find_element_by_xpath("//input[@value='PWFS' and @name='Type']").click()
    elif "aowfs" in Wavefront.lower() or "altair" in Wavefront.lower():
        driver.find_element_by_xpath("//input[@value='AOWFS' and @name='Type']").click()


#---------------------------------------------------------------------------------------------------

def setDetectorPropertiesNIFS(driver, Read, Coating, Wavefront):
    
    #Set read Mode and Well Depth
    if "bright" in Read.lower():
        driver.find_element_by_xpath("//input[@value='BRIGHT_OBJECT_SPEC' and @name='ReadMode']").click()
    elif "medium" in Read.lower():
        driver.find_element_by_xpath("//input[@value='MEDIUM_OBJECT_SPEC' and @name='ReadMode']").click()
    elif "faint" in Read.lower():
        driver.find_element_by_xpath("//input[@value='FAINT_OBJECT_SPEC' and @name='ReadMode']").click()
        
    #Set Mirror Coating
    if "silver" in Coating.lower():
        driver.find_element_by_xpath("//input[@value='SILVER' and @name='Coating']").click()
    elif "alum" in Coating.lower():
        driver.find_element_by_xpath("//input[@value='ALUMINIUM' and @name='Coating']").click()
     
    #Set Wavefront Sensor
    if "oiwfs" in Wavefront.lower():
        driver.find_element_by_xpath("//input[@value='OIWFS' and @name='Type']").click()
    elif "pwfs" in Wavefront.lower():
        driver.find_element_by_xpath("//input[@value='PWFS' and @name='Type']").click()
    elif "aowfs" in Wavefront.lower() or "altair" in Wavefront.lower():
        driver.find_element_by_xpath("//input[@value='AOWFS' and @name='Type']").click()


#---------------------------------------------------------------------------------------------------

def setDetectorPropertiesGNIRS(driver, Read, Coating, Wavefront):
    
    #Set read Mode and Well Depth
    if "verybright" in Read.lower():
        driver.find_element_by_xpath("//input[@value='VERY_BRIGHT' and @name='ReadMode']").click()
    elif "bright" in Read.lower():
        driver.find_element_by_xpath("//input[@value='BRIGHT' and @name='ReadMode']").click()
    elif "faint" in Read.lower():
        driver.find_element_by_xpath("//input[@value='FAINT' and @name='ReadMode']").click()
    elif "veryfaint" in Read.lower():
        driver.find_element_by_xpath("//input[@value='VERY_FAINT' and @name='ReadMode']").click()
        
    #Set Mirror Coating
    if "silver" in Coating.lower():
        driver.find_element_by_xpath("//input[@value='SILVER' and @name='Coating']").click()
    elif "alum" in Coating.lower():
        driver.find_element_by_xpath("//input[@value='ALUMINIUM' and @name='Coating']").click()
     
    #Set Wavefront Sensor
    if "oiwfs" in Wavefront.lower():
        driver.find_element_by_xpath("//input[@value='OIWFS' and @name='Type']").click()
    elif "pwfs" in Wavefront.lower():
        driver.find_element_by_xpath("//input[@value='PWFS' and @name='Type']").click()
    elif "aowfs" in Wavefront.lower() or "altair" in Wavefront.lower():
        driver.find_element_by_xpath("//input[@value='AOWFS' and @name='Type']").click()


#---------------------------------------------------------------------------------------------------
# For Michelle and TReCS

def setDetectorPropertiesMichelle(driver, Mirror, Port, Wavefront):
    
    #Set Mirror Coating
    if "silver" in Mirror.lower():
        driver.find_element_by_xpath("//input[@value='SILVER' and @name='Coating']").click()
    elif "alum" in Mirror.lower():
        driver.find_element_by_xpath("//input[@value='ALUMINIUM' and @name='Coating']").click()
        
    #Set Instrument Port
    if "side" in Port.lower():
        driver.find_element_by_xpath("//input[@value='SIDE_LOOKING' and @name='IssPort']").click()
    else:
        driver.find_element_by_xpath("//input[@value='UP_LOOKING' and @name='IssPort']").click()

    #Set Wavefront Sensor
    if "oiwfs" in Wavefront.lower():
        driver.find_element_by_xpath("//input[@value='OIWFS' and @name='Type']").click()
    elif "pwfs" in Wavefront.lower():
        driver.find_element_by_xpath("//input[@value='PWFS' and @name='Type']").click()
    elif "aowfs" in Wavefront.lower() or "altair" in Wavefront.lower():
        driver.find_element_by_xpath("//input[@value='AOWFS' and @name='Type']").click()


#---------------------------------------------------------------------------------------------------

def setOpticalPropertiesTReCS(driver, Cryostat, Filter, FPM, Grating, Wavelength):
    logger = logging.getLogger('setOpticalPropertiesTReCS')

    time.sleep(sleep)

    # Set Cryostat
    driver.find_element_by_xpath("//select[@name='WindowWheel']/option[@value='" + Cryostat + "']").click()
    
    # Set Filter
    driver.find_element_by_xpath("//select[@name='Filter']/option[@value='" + Filter + "']").click()

    # Set FPM
    driver.find_element_by_xpath("//select[@name='Mask']/option[@value='" + FPM + "']").click()
    
    # Set Grating
    driver.find_element_by_xpath("//select[@name='Disperser']/option[@value='" + Grating + "']").click() 
    
    # Set Spectrum Central Wavelength
    logger.debug('Setting central wavelength to %s um', Wavelength)
    driver.find_element_by_name("instrumentCentralWavelength").clear()  
    driver.find_element_by_name("instrumentCentralWavelength").send_keys(Wavelength)


#---------------------------------------------------------------------------------------------------

def setOpticalPropertiesMichelle(driver, Filter, FPM, Grating, Wavelength, Polarimetry):
    logger = logging.getLogger('setOpticalPropertiesMichelle')

    time.sleep(sleep)

    # Set Filter
    driver.find_element_by_xpath("//select[@name='Filter']/option[@value='" + Filter + "']").click()

    # Set FPM
    driver.find_element_by_xpath("//select[@name='Mask']/option[@value='" + FPM + "']").click()
    
    # Set Grating
    driver.find_element_by_xpath("//select[@name='Disperser']/option[@value='" + Grating + "']").click()

    # Set Spectrum Central Wavelength
    logger.debug('Setting central wavelength to %s um', Wavelength)
    driver.find_element_by_name("instrumentCentralWavelength").clear()  
    driver.find_element_by_name("instrumentCentralWavelength").send_keys(Wavelength)  
    
    # Set Polarimetry
    if "dis" in Polarimetry.lower():
        driver.find_element_by_xpath("//input[@value='NO' and @name='polarimetry']").click()
    else:
        driver.find_element_by_xpath("//input[@value='YES' and @name='polarimetry']").click()


#---------------------------------------------------------------------------------------------------

def setOpticalPropertiesNIFS(driver, Filter, Grating, Wavelength):
    logger = logging.getLogger('setOpticalPropertiesNIFS')

    time.sleep(sleep)

    # Set Filter
    if "zj" in Filter.lower() or "z-j" in Filter.lower():
        driver.find_element_by_xpath("//select[@name='Filter']/option[@value='ZJ_FILTER']").click()
    elif "jh" in Filter.lower() or "j-h" in Filter.lower() or "hj" in Filter.lower():
        driver.find_element_by_xpath("//select[@name='Filter']/option[@value='JH_FILTER']").click()
    elif "hk" in Filter.lower() or "h-k" in Filter.lower():
        driver.find_element_by_xpath("//select[@name='Filter']/option[@value='HK_FILTER']").click()
       
    # Set Grating
    if "z" in Grating.lower():
        driver.find_element_by_xpath("//select[@name='Disperser']/option[@value='Z']").click()
    elif "short" in Grating.lower():
        driver.find_element_by_xpath("//select[@name='Disperser']/option[@value='K_SHORT']").click()
    elif "long" in Grating.lower():   
        driver.find_element_by_xpath("//select[@name='Disperser']/option[@value='K_LONG']").click()
    elif "j" in Grating.lower():
        driver.find_element_by_xpath("//select[@name='Disperser']/option[@value='J']").click()
    elif "h" in Grating.lower():
        driver.find_element_by_xpath("//select[@name='Disperser']/option[@value='H']").click()
    else:
        driver.find_element_by_xpath("//select[@name='Disperser']/option[@value='K']").click()

    # Set Spectrum Central Wavelength
    if type(Wavelength) is float:
        Wavelength = str(Wavelength)
    logger.debug('Setting central wavelength to %s um', Wavelength)

    driver.find_element_by_name("instrumentCentralWavelength").clear()
    driver.find_element_by_name("instrumentCentralWavelength").send_keys(Wavelength)


#---------------------------------------------------------------------------------------------------

def setOpticalPropertiesGNIRS(driver, Camera, FPM, Grating, Wavelength, Cross):
    logger = logging.getLogger('setOpticalPropertiesGNIRS')

    time.sleep(sleep)

    # Set Camera
    driver.find_element_by_xpath("//select[@name='PixelScale']/option[@value='" + Camera + "']").click()
    
    # Set Focal Plane Mask
    driver.find_element_by_xpath("//select[@name='SlitWidth']/option[@value='" + FPM + "']").click()
    
    # Set Grating
    driver.find_element_by_xpath("//select[@name='Disperser']/option[@value='" + Grating + "']").click()
    
    # Set Central Wavelength
    if type(Wavelength) is float:
        Wavelength = str(Wavelength)
    logger.debug('Setting central wavelength to %s um', Wavelength)
    
    driver.find_element_by_name("instrumentCentralWavelength").clear()
    driver.find_element_by_name("instrumentCentralWavelength").send_keys(Wavelength)
    
    # Set Cross Dispersed
    if "no" in Cross.lower():
        driver.find_element_by_xpath("//select[@name='CrossDispersed']/option[@value='NO']").click()
    else:
        driver.find_element_by_xpath("//select[@name='CrossDispersed']/option[@value='SXD']").click()


#---------------------------------------------------------------------------------------------------

def setOpticalPropertiesGMOS(driver, Grating, Filter, CentralWavelength, FPU):
    logger = logging.getLogger('setOpticalPropertiesGMOS')

    time.sleep(sleep)
    
    # Set Grating
    driver.find_element_by_xpath("//select[@name='instrumentDisperser']/option[@value='" + Grating + "']").click()

    # Set Filter
    driver.find_element_by_xpath("//select[@name='instrumentFilter']/option[@value='" + Filter + "']").click()

    # Set Central Wavelength
    logger.debug('Setting central wavelength to %s nm', CentralWavelength)
    driver.find_element_by_name("instrumentCentralWavelength").clear()
    driver.find_element_by_name("instrumentCentralWavelength").send_keys(CentralWavelength)    

    # Alternatively:
    #cwav = driver.find_element_by_name("instrumentCentralWavelength")
    #cwav.clear()
    #cwav.send_keys(CentralWavelength)
    # or:
    #cwav = driver.find_element_by_xpath("//input[@name='instrumentCentralWavelength']")
    #cwav.clear()
    #cwav.send_keys(CentralWavelength)
    
    # Set Focal Plane Unit
    driver.find_element_by_xpath("//select[@name='instrumentFPMask']/option[@value='" + FPU + "']").click()


#---------------------------------------------------------------------------------------------------
# Bryan Miller, 2013-09-06

def setOpticalPropertiesGSAOI(driver, Filter):
        
    #Set Filter
    driver.find_element_by_xpath("//select[@name='Filter']/option[@value='" + Filter + "']").click()


#---------------------------------------------------------------------------------------------------
# Bryan Miller, 2013-09-10

def setOpticalPropertiesF2(driver, Filter, Disperser, FPM):
        
    time.sleep(sleep)

    #Set Filter
    driver.find_element_by_xpath("//select[@name='Filter']/option[@value='" + Filter + "']").click()
    
    #Set Disperser
    driver.find_element_by_xpath("//select[@name='Disperser']/option[@value='" + Disperser + "']").click()

    #Set FPM
    driver.find_element_by_xpath("//select[@name='FPUnit']/option[@value='" + FPM + "']").click()


#---------------------------------------------------------------------------------------------------

def setOpticalPropertiesNIRI(driver, Camera, Filter, Disperser, FPM):
    
    time.sleep(sleep)

    #Set Camera
    driver.find_element_by_xpath("//select[@name='Camera']/option[@value='" + Camera + "']").click()
    
    #Set Filter
    driver.find_element_by_xpath("//select[@name='Filter']/option[@value='" + Filter + "']").click()
    
    #Set Disperser
    driver.find_element_by_xpath("//select[@name='Disperser']/option[@value='" + Disperser + "']").click()

    #Set FPM
    driver.find_element_by_xpath("//select[@name='Mask']/option[@value='" + FPM + "']").click()


#---------------------------------------------------------------------------------------------------

def setAltairProperties(driver, Seperation, Brightness, FieldLens, Mode):

    #Set AO Guide Star Seperation
    if type(Seperation) is float:
        Seperation = str(Seperation)
    driver.find_element_by_name("guideSep").clear()
    driver.find_element_by_name("guideSep").send_keys(Seperation)  

    #Set Guide Star Brightness (R-Band)
    if type(Brightness) is float:
        Brightness = str(Brightness)
    driver.find_element_by_name("guideMag").clear()
    driver.find_element_by_name("guideMag").send_keys(Brightness) 

    #Set Field Lens
    driver.find_element_by_xpath("//input[@value='" + FieldLens.upper() + "' and @name='FieldLens']").click()
    
    #Set Altair Mode
    if "ngs" in Mode.lower() or "natural" in Mode.lower():
        driver.find_element_by_xpath("//input[@value='NGS' and @name='GuideStarType']").click()
    else:
        driver.find_element_by_xpath("//input[@value='LGS' and @name='GuideStarType']").click()


#---------------------------------------------------------------------------------------------------

def setObservingConditions(driver, ImageQuality, CloudCover, WaterVapour, SkyBackground, AirMass):
    
    #set Image Quality
    if ImageQuality == 20:
        Value = "PERCENT_20"
    elif ImageQuality == 70:
        Value = "PERCENT_70"
    elif ImageQuality == 85:
        Value = "PERCENT_85"
    else:
        Value = "ANY"
        
    driver.find_element_by_xpath("//input[@name='ImageQuality' and @value='" + Value + "']").click()
    
    #Set Cloud Cover
    if CloudCover == 50:
        Value = "PERCENT_50"
    elif CloudCover == 70:
        Value = "PERCENT_70"
    elif CloudCover == 80:
        Value = "PERCENT_80"
    else:
        Value = "ANY"
        
    driver.find_element_by_xpath("//input[@name='CloudCover' and @value='" + Value + "']").click()

    #Set Water Vapour
    if WaterVapour == 20:
        Value = "PERCENT_20"
    elif WaterVapour == 50:
        Value = "PERCENT_50"
    elif WaterVapour == 80:
        Value = "PERCENT_80"
    else:
        Value = "ANY"
        
    driver.find_element_by_xpath("//input[@name='WaterVapor' and @value='" + Value + "']").click()

    #Set Sky Background
    if SkyBackground == 20:
        Value = "PERCENT_20"
    elif SkyBackground == 50:
        Value = "PERCENT_50"
    elif SkyBackground == 80:
        Value = "PERCENT_80"
    else:
        Value = "ANY"   

    #If SkyBackground is set to 0, don't try to set it
    if not SkyBackground == 0:
        driver.find_element_by_xpath("//input[@name='SkyBackground' and @value='" + Value + "']").click()

    #Set Air Mass
    if type(AirMass) is int or type(AirMass) is float:
        AirMass = str(AirMass)
    driver.find_element_by_xpath("//input[@name='Airmass' and @value='" + AirMass + "']").click()


#---------------------------------------------------------------------------------------------------
# Calculation method for Michelle and TReCS

def setCalculationMethodMichelle(driver, ResultMethod, Value1, Fraction):
    
    #Set Fraction to a string
    Fraction = str(Fraction)
    Value1 = str(Value1)

    #Set Results Method, Total Integration or S/N Ratio
    if "ratio" in ResultMethod.lower():
        driver.find_element_by_xpath("//input[@value='s2n' and @name='calcMethod']").click()        
        driver.find_element_by_name("expTimeA").clear()
        driver.find_element_by_name("expTimeA").send_keys(Value1)
        driver.find_element_by_name("fracOnSourceA").clear()
        driver.find_element_by_name("fracOnSourceA").send_keys(Fraction)     
    else:
        #Choose Total Integration Time 
        driver.find_element_by_xpath("//input[@value='intTime' and @name='calcMethod']").click()
        driver.find_element_by_name("sigmaC").clear()
        driver.find_element_by_name("sigmaC").send_keys(Value1)
        driver.find_element_by_name("fracOnSourceC").clear()
        driver.find_element_by_name("fracOnSourceC").send_keys(Fraction)         


#---------------------------------------------------------------------------------------------------

def setCalculationMethod(driver, ResultMethod, Value1, Time, Fraction, Choose=True):
    # For instruments w/o coadd option

    #Set Fraction to a string
    Fraction = str(Fraction)
    Value1 = str(Value1)

    #Set the Results Method, Total Integration or S/N ratio
    if "ratio" in ResultMethod.lower():
        if Choose:
            driver.find_element_by_xpath("//input[@value='s2n' and @name='calcMethod']").click()
        driver.find_element_by_name("numExpA").clear()
        driver.find_element_by_name("numExpA").send_keys(Value1)
        driver.find_element_by_name("expTimeA").clear()
        driver.find_element_by_name("expTimeA").send_keys(Time)
        driver.find_element_by_name("fracOnSourceA").clear()
        driver.find_element_by_name("fracOnSourceA").send_keys(Fraction)
    else:
        driver.find_element_by_xpath("//input[@value='intTime' and @name='calcMethod']").click()
        driver.find_element_by_name("sigmaC").clear()
        driver.find_element_by_name("sigmaC").send_keys(Value1)
        driver.find_element_by_name("expTimeC").clear()
        driver.find_element_by_name("expTimeC").send_keys(Time)
        driver.find_element_by_name("fracOnSourceC").clear()
        driver.find_element_by_name("fracOnSourceC").send_keys(Fraction)


# ---------------------------------------------------------------------------------------------------

def setCalculationMethodCoadd(driver, ResultMethod, Value1, Ncoadd, Time, Fraction, Choose=True):
    # For instruments with a coadd option

    # Set Fraction to a string
    Fraction = str(Fraction)
    Ncoadd = str(Ncoadd)
    Value1 = str(Value1)

    # Set the Results Method, Total Integration or S/N ratio
    if "ratio" in ResultMethod.lower():
        if Choose:
            driver.find_element_by_xpath("//input[@value='s2n' and @name='calcMethod']").click()
            driver.find_element_by_name("numExpA").clear()
            driver.find_element_by_name("numExpA").send_keys(Value1)
            driver.find_element_by_name("numCoaddsA").clear()
            driver.find_element_by_name("numCoaddsA").send_keys(Ncoadd)
            driver.find_element_by_name("expTimeA").clear()
            driver.find_element_by_name("expTimeA").send_keys(Time)
            driver.find_element_by_name("fracOnSourceA").clear()
            driver.find_element_by_name("fracOnSourceA").send_keys(Fraction)
        else:
            driver.find_element_by_xpath("//input[@value='intTime' and @name='calcMethod']").click()
            driver.find_element_by_name("sigmaC").clear()
            driver.find_element_by_name("sigmaC").send_keys(Value1)
            driver.find_element_by_name("numCoaddsC").clear()
            driver.find_element_by_name("numCoaddsC").send_keys(Ncoadd)
            driver.find_element_by_name("expTimeC").clear()
            driver.find_element_by_name("expTimeC").send_keys(Time)
            driver.find_element_by_name("fracOnSourceC").clear()
            driver.find_element_by_name("fracOnSourceC").send_keys(Fraction)


#---------------------------------------------------------------------------------------------------
# Slit Length is only for user defined aperture
# If using optimum aperture, only pass 3 arguments (driver,Type,Times)
# Used for GMOS, Michelle and TReCS

def setAnalysisMethodGMOS(driver, Type, Times, SlitLength=0):
    
    if type(SlitLength) is float:
        SlitLength = str(SlitLength)
   
    if type(Times) is float:
        Times = str(Times)
   
    if "optimum" in Type.lower() or "ratio" in Type.lower() or "s/n" in Type.lower():
        driver.find_element_by_xpath("//input[@value='autoAper' and @name='analysisMethod']").click()
        driver.find_element_by_name("autoSkyAper").clear()
        driver.find_element_by_name("autoSkyAper").send_keys(Times)
    else:
        driver.find_element_by_xpath("//input[@value='userAper' and @name='analysisMethod']").click()
        driver.find_element_by_name("userAperDiam").clear()
        driver.find_element_by_name("userAperDiam").send_keys(SlitLength)
        driver.find_element_by_name("userSkyAper").clear()
        driver.find_element_by_name("userSkyAper").send_keys(Times)  


#---------------------------------------------------------------------------------------------------
# Analysis Method procedure for most instruments other than GMOS

def setAnalysisMethod(driver, Type, Slitlength=0):
    
    if type(Slitlength) is float:
        Slitlength = str(Slitlength)

    if "optimum" in Type.lower() or "ratio" in Type.lower() or "s/n" in Type.lower():
        #Set for Optimum S/N Ratio
        driver.find_element_by_xpath("//input[@value='autoAper' and @name='aperType']").click()
    else:
        #Set for Apeture of diameter( slit length) = X
        driver.find_element_by_xpath("//input[@value='userAper' and @name='aperType']").click()
        driver.find_element_by_name("userAperDiam").clear()
        driver.find_element_by_name("userAperDiam").send_keys(Slitlength)


# ---------------------------------------------------------------------------------------------------
# Analysis Method procedure for most instruments other than GMOS

def setAnalysisMethodGSAOI(driver, Type, Offset=5.0, largeSkyOffset=0, aperDiam=2.0):
    if type(Offset) is float:
        Offset = str(Offset)

    if type(largeSkyOffset) is int:
        largeSkyOffset = str(largeSkyOffset)

    if type(aperDiam) is float:
        aperDiam = str(aperDiam)

    driver.find_element_by_name("offset").clear()
    driver.find_element_by_name("offset").send_keys(Offset)
    driver.find_element_by_name("largeSkyOffset").clear()
    driver.find_element_by_name("largeSkyOffset").send_keys(largeSkyOffset)

    if "optimum" in Type.lower() or "ratio" in Type.lower() or "s/n" in Type.lower():
        # Set for Optimum S/N Ratio
        driver.find_element_by_xpath("//input[@value='autoAper']").click()
    else:
        # Set for Apeture of diameter( slit length) = X
        driver.find_element_by_xpath("//input[@value='userAper' and @name='aperType']").click()
        driver.find_element_by_name("userAperDiam").clear()
        driver.find_element_by_name("userAperDiam").send_keys(aperDiam)


# ---------------------------------------------------------------------------------------------------

def setIFUSpectroscopy(driver, Type, Offset1, Offset2=0):
    
    #Change Offsets to strings
    if type(Offset1) is float:
        Offset1 = str(Offset1)
    if type(Offset2) is float:
        Offset2 = str(Offset2)        
    
    #Choose the type
    if "sum" in Type.lower():
        driver.find_element_by_xpath("//input[@value='summedIFU' and @name='ifuMethod']").click()
        driver.find_element_by_name("ifuNumX").clear()
        driver.find_element_by_name("ifuNumX").send_keys(Offset1)          
        driver.find_element_by_name("ifuNumY").clear()
        driver.find_element_by_name("ifuNumY").send_keys(Offset2)         
    elif "multi" in Type.lower():
        #Choose Multiple IFU elements
        driver.find_element_by_xpath("//input[@value='radialIFU' and @name='ifuMethod']").click()
        driver.find_element_by_name("ifuMinOffset").clear()
        driver.find_element_by_name("ifuMinOffset").send_keys(Offset1)          
        driver.find_element_by_name("ifuMaxOffset").clear()
        driver.find_element_by_name("ifuMaxOffset").send_keys(Offset2) 
    else:
        #Choose individual IFU element
        driver.find_element_by_xpath("//input[@value='singleIFU' and @name='ifuMethod']").click()
        driver.find_element_by_name("ifuOffset").clear()
        driver.find_element_by_name("ifuOffset").send_keys(Offset1)        


#---------------------------------------------------------------------------------------------------

def calculate(driver):
    
    #Click Calculate button
    driver.find_element_by_xpath("//input[@value='Calculate' and @type='submit']").click()


#---------------------------------------------------------------------------------------------------

def extractData(driver, Type, TestNumber, Instrument, Testing, Cross=False):
    logger = logging.getLogger('extractData')

    # Turn TestNumber into a str
    if type(TestNumber) is int:
        TestNumber = str(TestNumber)

    # Check if Folders exist to save to, else create them
    path = GetPath(Instrument, Testing)
    if not os.path.exists(path):
        os.mkdir(path)
    
    FileLocation = path + '/Test' + TestNumber
    
    # If using GNIRS Cross-Dispersed, no need to check Single Exposure S/N
    if Cross:
        FileList = ("signal spectrum", "background spectrum", "Final")
    else:
        FileList = ("signal spectrum", "background spectrum", "Single Exposure", "Final")

    # Generate list of all open windows:
    windowsList =  driver.window_handles

    # Switch to results window:
    driver.switch_to.window(windowsList[1])
    
    # Imaging
    if "imag" in Type.lower():
        pass
    # Spectroscopy
    else:
        for fileToSave in FileList:
            logger.debug('fileToSave = %s', fileToSave)
            fileObject = driver.find_element_by_partial_link_text(fileToSave)
            fileLink = fileObject.get_attribute("href")
            logger.debug('fileLink = %s', fileLink)

            # Open the file and write to output
            u = urlopen(fileLink)
            localFile = open(FileLocation + '-' + fileToSave.replace(' ','') + '.dat', 'wb')
            localFile.write(u.read())
            localFile.close()
        pass
    
    # Save the results page
    pageData = driver.page_source
    localFile = open(FileLocation + '-output.html', 'w')
    localFile.write(pageData)
    localFile.close()
    
    #if not Archiving:
    #    compareData(driver,Type,TestNumber,Instrument,Cross)


#---------------------------------------------------------------------------------------------------

def ConfigureLogging(logfile=None, filelevel='INFO', screenlevel='INFO'):

     logger = logging.getLogger()

     # DEBUG     Detailed information, typically of interest only whendiagnosing problems.
     # INFO      Confirmation that things are working as expected.
     # WARNING   An indication that something unexpected happened, orindicative of some problem in the near future.
     # ERROR     Due to a more serious problem, the software has notbeen able to perform some function.
     # CRITICAL  A serious error, indicating that the program itself maybe unable to continue running.

     # set minimum threshold level for logger:
     logger.setLevel(logging.DEBUG)

     # create formatter and add it to the handlers:
     #formatter = logging.Formatter('%(asctime)s %(name)-10s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
     formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

     if logfile: # create file handler:
         logfilehandler = logging.FileHandler(logfile)
         if filelevel.upper() == 'DEBUG':
             logfilehandler.setLevel(logging.DEBUG)
         elif filelevel.upper() == 'INFO':
             logfilehandler.setLevel(logging.INFO)
         elif filelevel.upper() == 'WARNING':
             logfilehandler.setLevel(logging.WARNING)
         elif filelevel.upper() == 'ERROR':
             logfilehandler.setLevel(logging.ERROR)
         elif filelevel.upper() == 'CRITICAL':
             logfilehandler.setLevel(logging.CRITICAL)
         else:
             print ('ERROR: Unknown log error level')
             logfilehandler.setLevel(logging.INFO)
         logfilehandler.setFormatter(formatter)
         logger.addHandler(logfilehandler)

     # create console screen log handler:
     consoleloghandler = logging.StreamHandler()
     if screenlevel.upper() == 'DEBUG':
         consoleloghandler.setLevel(logging.DEBUG)
     elif screenlevel.upper() == 'INFO':
         consoleloghandler.setLevel(logging.INFO)
     elif screenlevel.upper() == 'WARNING':
         consoleloghandler.setLevel(logging.WARNING)
     elif screenlevel.upper() == 'ERROR':
         consoleloghandler.setLevel(logging.ERROR)
     elif screenlevel.upper() == 'CRITICAL':
         consoleloghandler.setLevel(logging.CRITICAL)
     else:
         print ('ERROR: Unknown log error level')
         consoleloghandler.setLevel(logging.INFO)
     consoleloghandler.setFormatter(formatter)
     logger.addHandler(consoleloghandler)

     return(logger)


#---------------------------------------------------------------------------------------------------

