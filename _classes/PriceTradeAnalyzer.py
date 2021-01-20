#These settings can be configured in a global config.ini in the program root directory under [Settings]
useWebProxyServer = False	#If you need a web proxy to browse the web
nonGUIEnvironment = False	#hosted environments often have no GUI so matplotlib won't be outputting to display
suspendPriceLoads = False

#pip install any of these if they are missing
import time, random, os, ssl, matplotlib
import numpy as np, pandas as pd
from math import floor
from datetime import datetime, timedelta
from pandas.tseries.offsets import BDay
import urllib.request as webRequest
from _classes.Utility import *

#pricingData and TradingModel are the two intended exportable classes
#user input dates are expected to be in local format, after that they should be in database format
#-------------------------------------------- Global settings -----------------------------------------------
nonGUIEnvironment = ReadConfigBool('Settings', 'nonGUIEnvironment')
if nonGUIEnvironment: matplotlib.use('agg',warn=False, force=True)
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
currentProxyServer = None
proxyList = ['173.232.228.25:8080']
useWebProxyServer = ReadConfigBool('Settings', 'useWebProxyServer')
if useWebProxyServer: 
	x =  ReadConfigList('Settings', 'proxyList')
	if not x == None: proxyList = x		

BaseFieldList = ['Open','Close','High','Low']
#-------------------------------------------- General Utilities -----------------------------------------------
def PandaIsInIndex(df:pd.DataFrame, value):
	try:
		x = df.loc[value]
		r = True
	except:
		r = False
	return r


def PlotSetDefaults():
	#params = {'legend.fontsize': 4, 'axes.labelsize': 4,'axes.titlesize':4,'xtick.labelsize':4,'ytick.labelsize':4}
	#plt.rcParams.update(params)
	plt.rcParams['font.size'] = 4

def PlotScalerDateAdjust(minDate:datetime, maxDate:datetime, ax):
	if type(minDate)==str:
		daysInGraph = DateDiffDays(minDate,maxDate)
	else:
		daysInGraph = (maxDate-minDate).days
	if daysInGraph >= 365*3:
		majorlocator =  mdates.YearLocator()
		minorLocator = mdates.MonthLocator()
		majorFormatter = mdates.DateFormatter('%m/%d/%Y')
	elif daysInGraph >= 365:
		majorlocator =  mdates.MonthLocator()
		minorLocator = mdates.WeekdayLocator()
		majorFormatter = mdates.DateFormatter('%m/%d/%Y')
	elif daysInGraph < 90:
		majorlocator =  mdates.DayLocator()
		minorLocator = mdates.DayLocator()
		majorFormatter =  mdates.DateFormatter('%m/%d/%Y')
	else:
		majorlocator =  mdates.WeekdayLocator()
		minorLocator = mdates.DayLocator()
		majorFormatter =  mdates.DateFormatter('%m/%d/%Y')
	ax.xaxis.set_major_locator(majorlocator)
	ax.xaxis.set_major_formatter(majorFormatter)
	ax.xaxis.set_minor_locator(minorLocator)
	#ax.xaxis.set_minor_formatter(daysFmt)
	ax.set_xlim(minDate, maxDate)

def PlotDataFrame(df:pd.DataFrame, title:str, xlabel:str, ylabel:str, adjustScale:bool=True, fileName:str = '', dpi:int = 600):
	if df.shape[0] >= 4:
		PlotSetDefaults()
		ax=df.plot(title=title, linewidth=.75)
		ax.set_xlabel(xlabel)
		ax.set_ylabel(ylabel)
		ax.tick_params(axis='x', rotation=70)
		ax.grid(b=True, which='major', color='black', linestyle='solid', linewidth=.5)
		ax.grid(b=True, which='minor', color='0.65', linestyle='solid', linewidth=.3)
		if adjustScale:
			dates= df.index.get_level_values('Date')
			minDate = dates.min()
			maxDate = dates.max()
			PlotScalerDateAdjust(minDate, maxDate, ax)
		if not fileName =='':
			if not fileName[-4] == '.': fileName+= '.png'
			plt.savefig(fileName, dpi=dpi)			
		else:
			fig = plt.figure(1)
			fig.canvas.set_window_title(title)
			plt.show()
		plt.close('all')

def GetProxiedOpener():
	testURL = 'https://stooq.com'
	userName, password = 'mUser', 'SecureAccess'
	context = ssl._create_unverified_context()
	handler = webRequest.HTTPSHandler(context=context)
	i = -1
	functioning = False
	global currentProxyServer
	while not functioning and i < len(proxyList):
		if i >=0 or currentProxyServer==None: currentProxyServer = proxyList[i]
		proxy = webRequest.ProxyHandler({'https': r'http://' + userName + ':' + password + '@' + currentProxyServer})
		auth = webRequest.HTTPBasicAuthHandler()
		opener = webRequest.build_opener(proxy, auth, handler) 
		opener.addheaders = [('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.1 Safari/603.1.30')]
		#opener.addheaders = [('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1.1 Safari/605.1.15')]	
		#opener.addheaders = [('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/18.17763')]
		try:
			conn = opener.open(testURL)
			print('Proxy ' + currentProxyServer + ' is functioning')
			functioning = True
		except:
			print('Proxy ' + currentProxyServer + ' is not responding')
		i+=1
	return opener

#-------------------------------------------- Classes -----------------------------------------------
class PlotHelper:
	def PlotDataFrame(self, df:pd.DataFrame, title:str='', xlabel:str='', ylabel:str='', adjustScale:bool=True, fileName:str = '', dpi:int=600): PlotDataFrame(df, title, xlabel, ylabel, adjustScale, fileName, dpi)

	def PlotDataFrameDateRange(self, df:pd.DataFrame, endDate:datetime=None, historyDays:int=90, title:str='', xlabel:str='', ylabel:str='', fileName:str = '', dpi:int=600):
		if df.shape[0] > 10: 
			if endDate==None: endDate=df.index[-1] 	#The latest date in the dataframe assuming ascending order				
			endDate = ToDateTime(endDate)
			startDate = endDate - BDay(historyDays)
			df = df[df.index >= startDate]
			df = df[df.index <= endDate]
			PlotDataFrame(df, title, xlabel, ylabel, True, fileName, dpi)
	
class PriceSnapshot:
	ticker=''
	high=0
	low=0
	open=0
	close=0
	oneDayAverage=0
	twoDayAverage=0
	fiveDayAverage=0
	shortEMA=0
	shortEMASlope=0
	longEMA=0
	longEMASlope=0
	channelHigh=0
	channelLow=0
	oneDayApc = 0
	oneDayDeviation=0
	fiveDayDeviation=0
	fifteenDayDeviation=0
	dailyGain=0
	monthlyGain=0
	monthlyLossStd=0
	estLow=0
	nextDayTarget=0
	estHigh=0
	snapShotDate=None
	
class PricingData:
	#Historical prices for a given stock, along with statistics, and future estimated prices
	stockTicker = ''
	historicalPrices = None	#dataframe with price history indexed on date
	pricePredictions = None #dataframe with price predictions indexed on date
	historyStartDate = None
	historyEndDate = None
	pricesLoaded = False
	statsLoaded = False
	predictionsLoaded = False
	predictionDeviation = 0	#Average percentage off from target
	pricesNormalized = False
	pricesInPercentages = False
	_dataFolderhistoricalPrices = 'data/historical/'
	_dataFolderCharts = 'data/charts/'
	_dataFolderDailyPicks = 'data/dailypicks/'
	
	def __init__(self, ticker:str, dataFolderRoot:str=''):
		self.stockTicker = ticker
		if not dataFolderRoot =='':
			if CreateFolder(dataFolderRoot):
				if not dataFolderRoot[-1] =='/': dataFolderRoot += '/'
				self._dataFolderCharts = dataFolderRoot + 'charts/'
				self._dataFolderhistoricalPrices = dataFolderRoot + 'historical/'
				self._dataFolderDailyPicks = dataFolderRoot + 'dailypicks/'
		else: CreateFolder('data')
		CreateFolder(self._dataFolderhistoricalPrices)
		CreateFolder(self._dataFolderCharts)
		CreateFolder(self._dataFolderDailyPicks)
		self.pricesLoaded = False
		self.statsLoaded = False
		self.predictionsLoaded = False
		self.historicalPrices = None	
		self.pricePredictions = None
		self.historyStartDate = None
		self.historyEndDate = None

	def __del__(self):
		self.pricesLoaded = False
		self.statsLoaded = False
		self.predictionsLoaded = False
		self.historicalPrices = None	
		self.pricePredictions = None
		self.historyStartDate = None
		self.historyEndDate = None

	def PrintStatus(self):
		print("pricesLoaded=" + str(self.pricesLoaded))
		print("statsLoaded=" + str(self.statsLoaded))
		print("historyStartDate=" + str(self.historyStartDate))
		print("historyEndDate=" + str(self.historyEndDate))
		
	def _DownloadPriceData(self,verbose:bool=False):
		url = "https://stooq.com/q/d/l/?i=d&s=" + self.stockTicker + '.us'
		if self.stockTicker[0] == '^': url = "https://stooq.com/q/d/l/?i=d&s=" + self.stockTicker 
		filePath = self._dataFolderhistoricalPrices + self.stockTicker + '.csv'
		s1 = ''
		if CreateFolder(self._dataFolderhistoricalPrices): filePath = self._dataFolderhistoricalPrices + self.stockTicker + '.csv'
		try:
			if useWebProxyServer:
				opener = GetProxiedOpener()
				openUrl = opener.open(url)
			else:
				openUrl = webRequest.urlopen(url) 
			r = openUrl.read()
			openUrl.close()
			s1 = r.decode()
			s1 = s1.replace(chr(13),'')
		except Exception as e:
			if verbose: print('Web connection error: ', e)
		if len(s1) < 1024:
			if verbose: print(' No data found online for ticker ' + self.stockTicker, url)
			if useWebProxyServer:
				global currentProxyServer
				global proxyList
				if not currentProxyServer==None and len(proxyList) > 3: 
					if verbose: print( 'Removing proxy: ', currentProxyServer)
					proxyList.remove(currentProxyServer)
					currentProxyServer = None
		else:
			if verbose: print(' Downloaded new data for ticker ' + self.stockTicker)
			f = open(filePath,'w')
			f.write(s1)
			f.close()

	def _LoadHistory(self, refreshPrices:bool=False,verbose:bool=False):
		self.pricesLoaded = False
		filePath = self._dataFolderhistoricalPrices + self.stockTicker + '.csv'
		if not os.path.isfile(filePath) or refreshPrices: self._DownloadPriceData(verbose=verbose)
		if os.path.isfile(filePath):
			df = pd.read_csv(filePath, index_col=0, parse_dates=True, na_values=['nan'])
			if (df.shape[0] > 0) and all([item in df.columns for item in BaseFieldList]): #Rows more than zero and base fields all exist
				df = df[BaseFieldList]
				df['Average'] = df.loc[:,BaseFieldList].mean(axis=1) #select those rows, calculate the mean value
				if (df['Open'] < df['Low']).any() or (df['Close'] < df['Low']).any() or (df['High'] < df['Low']).any() or (df['Open'] > df['High']).any() or (df['Close'] > df['High']).any(): 
					if verbose:
						print(self.stockTicker)
						print(df.loc[df['Low'] > df['High']])
						print(' Data validation error, Low > High.  Dropping values..')
					df = df.loc[df['Low'] <= df['High']]
					df = df.loc[df['Low'] <= df['Open']]
					df = df.loc[df['Low'] <= df['Close']]
					df = df.loc[df['High'] >= df['Open']]
					df = df.loc[df['High'] >= df['Close']]
				self.historicalPrices = df
				self.historyStartDate = self.historicalPrices.index.min()
				self.historyEndDate = self.historicalPrices.index.max()
				self.pricesLoaded = True
		if not self.pricesLoaded:
			print(' No data found for ' + self.stockTicker)
		return self.pricesLoaded 
		
	def LoadHistory(self, requestedStartDate:datetime=None, requestedEndDate:datetime=None, verbose:bool=False):
		self._LoadHistory(refreshPrices=False, verbose=verbose)
		if self.pricesLoaded:
			requestNewData = False
			filePath = self._dataFolderhistoricalPrices + self.stockTicker + '.csv'
			lastUpdated = datetime.fromtimestamp(os.path.getmtime(filePath))
			if DateDiffHours(lastUpdated, datetime.now()) > 12 and not suspendPriceLoads:	#Limit how many times per hour we refresh the data to prevent abusing the source
				if not(requestedStartDate==None): requestNewData = (requestedStartDate < self.historyStartDate)
				if not(requestedEndDate==None): requestNewData = (requestNewData or (self.historyEndDate < requestedEndDate))
				if requestNewData and verbose: print(' Requesting new data for ' + self.stockTicker + ' (requestedStart, historyStart, historyEnd, requestedEnd)', requestedStartDate, self.historyStartDate, self.historyEndDate, requestedEndDate)
				if (requestedStartDate==None and requestedEndDate==None):
					requestNewData = (DateDiffDays(startDate=lastUpdated, endDate=datetime.now()) > 1)
				if verbose: print(' Requesting new data ' + self.stockTicker + ' reason stale data ', lastUpdated)
			if requestNewData: self._LoadHistory(refreshPrices=True, verbose=verbose)
			if not(requestedStartDate==None): 
				if (requestedEndDate==None): requestedEndDate = self.historyEndDate
				self.TrimToDateRange(requestedStartDate, requestedEndDate)
		return(self.pricesLoaded)

	def TrimToDateRange(self,startDate:datetime, endDate:datetime):
		startDate = ToDateTime(startDate)
		startDate -= timedelta(days=45) #If we do not include earlier dates we can not calculate all the stats
		endDate = ToDateTime(endDate)
		self.historicalPrices = self.historicalPrices[(self.historicalPrices.index >= startDate) & (self.historicalPrices.index <= endDate)]
		self.historyStartDate = self.historicalPrices.index.min()
		self.historyEndDate = self.historicalPrices.index.max()
		#rint(self.stockTicker, 'trim to ', startDate, endDate, self.historyStartDate, self.historyEndDate, len(self.historicalPrices))
		
	def ConvertToPercentages(self):
		if self.pricesInPercentages:
			self.historicalPrices.iloc[0] = self.CTPFactor
			for i in range(1, self.historicalPrices.shape[0]):
				self.historicalPrices.iloc[i] = (1 + self.historicalPrices.iloc[i]) * self.historicalPrices.iloc[i-1]
			if self.predictionsLoaded:
				self.pricePredictions.iloc[0] = self.CTPFactor['Average']
				for i in range(1, self.pricePredictions.shape[0]):
					self.pricePredictions.iloc[i] = (1 + self.pricePredictions.iloc[i]) * self.pricePredictions.iloc[i-1]
			self.pricesInPercentages = False
			print(' Prices have been converted back from percentages.')
		else:
			self.CTPFactor = self.historicalPrices.iloc[0]
			self.historicalPrices = self.historicalPrices[['Open','Close','High','Low','Average']].pct_change(1)
			self.historicalPrices[:1] = 0
			if self.predictionsLoaded:
				self.pricePredictions = self.pricePredictions.pct_change(1)
			self.statsLoaded = False
			self.pricesInPercentages = True
			print(' Prices have been converted to percentage change from previous day.')
		
	def NormalizePrices(self, verbose:bool=False):
		#(x-min(x))/(max(x)-min(x))
		x = self.historicalPrices
		if not self.pricesNormalized:
			low = x['Low'].min(axis=0) - .000001 #To prevent div zero calculation errors.
			high = x['High'].max(axis=0)
			diff = high-low
			x['Open'] = (x['Open']-low)/diff
			x['Close'] = (x['Close']-low)/diff
			x['High'] = (x['High']-low)/diff
			x['Low'] = (x['Low']-low)/diff
			if self.predictionsLoaded:
				self.pricePredictions[['estLow']] = (self.pricePredictions[['estLow']]-low)/diff
				self.pricePredictions[['estAverage']] = (self.pricePredictions[['estAverage']]-low)/diff
				self.pricePredictions[['estHigh']] = (self.pricePredictions[['estHigh']]-low)/diff
			self.PreNormalizationLow = low
			self.PreNormalizationHigh = high
			self.PreNormalizationDiff = diff
			self.pricesNormalized = True
			if verbose: print(' Prices have been normalized.')
		else:
			low = self.PreNormalizationLow
			high = self.PreNormalizationHigh 
			diff = self.PreNormalizationDiff
			x['Open'] = (x['Open'] * diff) + low
			x['Close'] = (x['Close'] * diff) + low
			x['High'] = (x['High'] * diff) + low
			x['Low'] = (x['Low'] * diff) + low
			if self.predictionsLoaded:
				self.pricePredictions[['estLow']] = (self.pricePredictions[['estLow']] * diff) + low
				self.pricePredictions[['estAverage']] = (self.pricePredictions[['estAverage']] * diff) + low
				self.pricePredictions[['estHigh']] = (self.pricePredictions[['estHigh']] * diff) + low
			self.pricesNormalized = False
			if verbose: print(' Prices have been un-normalized.')
		x['Average'] = (x['Open'] + x['Close'] + x['High'] + x['Low'])/4
		#x['Average'] = x.loc[:,BaseFieldList].mean(axis=1, skipna=True) #Wow, this doesn't work.
		if (x['Average'] < x['Low']).any() or (x['Average'] > x['High']).any(): 
			print(x.loc[x['Average'] < x['Low']])
			print(x.loc[x['Average'] > x['High']])
			print(x.loc[x['Low'] > x['High']])
			print(self.PreNormalizationLow, self.PreNormalizationHigh, self.PreNormalizationDiff, self.PreNormalizationHigh-self.PreNormalizationLow)
			#print(x.loc[:,BaseFieldList].mean(axis=1))
			print('Stop: averages not computed correctly.')
			assert(False)
		self.historicalPrices = x
		if self.statsLoaded: self.CalculateStats()
		if verbose: print(self.historicalPrices[:1])

	def CalculateStats(self):
		if not self.pricesLoaded: self.LoadHistory()
		self.historicalPrices['2DayAv'] = self.historicalPrices['Average'].rolling(window=2, center=False).mean()
		self.historicalPrices['5DayAv'] = self.historicalPrices['Average'].rolling(window=5, center=False).mean()
		self.historicalPrices['shortEMA'] =  self.historicalPrices['Average'].ewm(com=3,min_periods=0,adjust=True,ignore_na=False).mean()
		self.historicalPrices['shortEMASlope'] = (self.historicalPrices['shortEMA']/self.historicalPrices['shortEMA'].shift(1))-1
		self.historicalPrices['longEMA'] = self.historicalPrices['Average'].ewm(com=9,min_periods=0,adjust=True,ignore_na=False).mean()
		self.historicalPrices['longEMASlope'] = (self.historicalPrices['longEMA']/self.historicalPrices['longEMA'].shift(1))-1
		self.historicalPrices['45dEMA'] = self.historicalPrices['Average'].ewm(com=22,min_periods=0,adjust=True,ignore_na=False).mean()
		self.historicalPrices['45dEMASlope'] = (self.historicalPrices['45dEMA']/self.historicalPrices['45dEMA'].shift(1))-1
		self.historicalPrices['1DayDeviation'] = (self.historicalPrices['High'] - self.historicalPrices['Low'])/self.historicalPrices['Low']
		self.historicalPrices['5DavDeviation'] = self.historicalPrices['1DayDeviation'].rolling(window=5, center=False).mean()
		self.historicalPrices['15DavDeviation'] = self.historicalPrices['1DayDeviation'].rolling(window=15, center=False).mean()
		self.historicalPrices['1DayApc'] = ((self.historicalPrices['Average'] - self.historicalPrices['Average'].shift(1)) / self.historicalPrices['Average'].shift(1))
		self.historicalPrices['3DayApc'] = self.historicalPrices['1DayApc'].rolling(window=3, center=False).mean()
		self.historicalPrices['dailyGain'] = (self.historicalPrices['5DayAv'] / self.historicalPrices['5DayAv'].shift(1))-1
		self.historicalPrices['monthlyGain'] = (self.historicalPrices['5DayAv'] / self.historicalPrices['5DayAv'].shift(20))-1
		#self.historicalPrices['monthlyGainStd'] = self.historicalPrices['monthlyGain'].rolling(window=253, center=False).std()
		self.historicalPrices['monthlyLosses'] = self.historicalPrices['monthlyGain']
		self.historicalPrices['monthlyLosses'].loc[self.historicalPrices['monthlyLosses'] > 0] = 0 #zero out the positives
		self.historicalPrices['monthlyLossStd'] = self.historicalPrices['monthlyLosses'].rolling(window=253, center=False).std()	#Stdev of negative values, these are the negative monthly price drops in the past year
		self.historicalPrices['1DayMomentum'] = (self.historicalPrices['Average'] / self.historicalPrices['Average'].shift(1))-1
		self.historicalPrices['3DayMomentum'] = (self.historicalPrices['Average'] / self.historicalPrices['Average'].shift(3))-1
		self.historicalPrices['5DayMomentum'] = (self.historicalPrices['Average'] / self.historicalPrices['Average'].shift(5))-1
		self.historicalPrices['10DayMomentum'] = (self.historicalPrices['Average'] / self.historicalPrices['Average'].shift(10))-1
		self.historicalPrices['channelHigh'] = self.historicalPrices['longEMA'] + (self.historicalPrices['Average']*self.historicalPrices['15DavDeviation'])
		self.historicalPrices['channelLow'] = self.historicalPrices['longEMA'] - (self.historicalPrices['Average']*self.historicalPrices['15DavDeviation'])
		self.historicalPrices.fillna(method='ffill', inplace=True)
		self.historicalPrices.fillna(method='bfill', inplace=True)
		self.statsLoaded = True
		return True

	def MonthyReturnVolatility(self): return self.historicalPrices['MonthlyGain'].rolling(window=253, center=False).std() #of the past year

	def SaveStatsToFile(self, includePredictions:bool=False, verbose:bool=False):
		if includePredictions:
			filePath = self._dataFolderhistoricalPrices + self.stockTicker + '_stats_predictions.csv'
			r = self.historicalPrices.join(self.pricePredictions, how='outer') #, rsuffix='_Predicted'
			r.to_csv(filePath)
		else:
			filePath = self._dataFolderhistoricalPrices + self.stockTicker + '_stats.csv'
			self.historicalPrices.to_csv(filePath)
		print('Statistics saved to: ' + filePath)
		
	def PredictPrices(self, method:int=1, daysIntoFuture:int=1, NNTrainingEpochs:int=0):
		#Predict current prices from previous days info
		self.predictionsLoaded = False
		self.pricePredictions = pd.DataFrame()	#Clear any previous data
		if not self.statsLoaded: self.CalculateStats()
		if method < 3:
			minActionableSlope = 0.001
			if method==0:	#Same as previous day
				self.pricePredictions = pd.DataFrame()
				self.pricePredictions['estLow'] =  self.historicalPrices['Low'].shift(1)
				self.pricePredictions['estHigh'] = self.historicalPrices['High'].shift(1)
			elif method==1 :	#Slope plus momentum with some consideration for trend.
					#++,+-,-+,==
				bucket = self.historicalPrices.copy()
				bucket['estLow']  = bucket['Average'].shift(1) * (1-bucket['15DavDeviation']/2) + (abs(bucket['1DayApc'].shift(1)))
				bucket['estHigh'] = bucket['Average'].shift(1) * (1+bucket['15DavDeviation']/2) + (abs(bucket['1DayApc'].shift(1)))
				bucket = bucket.query('longEMASlope >= -' + str(minActionableSlope) + ' or shortEMASlope >= -' + str(minActionableSlope)) #must filter after rolling calcuations
				bucket = bucket[['estLow','estHigh']]
				self.pricePredictions = bucket
					#-- downward trend
				bucket = self.historicalPrices.copy()
				bucket['estLow'] = bucket['Low'].shift(1).rolling(3).min() * .99
				bucket['estHigh'] = bucket['High'].shift(1).rolling(3).min() 
				bucket = bucket.query('not (longEMASlope >= -' + str(minActionableSlope) + ' or shortEMASlope >= -' + str(minActionableSlope) +')')
				bucket = bucket[['estLow','estHigh']]
				self.pricePredictions = self.pricePredictions.append(bucket)
				self.pricePredictions.sort_index(inplace=True)	
			elif method==2:	#Slope plus momentum with full consideration for trend.
					#++ Often over bought, strong momentum
				bucket = self.historicalPrices.copy() 
				#bucket['estLow']  = bucket['Low'].shift(1).rolling(4).max()  * (1 + abs(bucket['shortEMASlope'].shift(1)))
				#bucket['estHigh'] = bucket['High'].shift(1).rolling(4).max()  * (1 + abs(bucket['shortEMASlope'].shift(1)))
				bucket['estLow']  = bucket['Low'].shift(1).rolling(4).max()  + (abs(bucket['1DayApc'].shift(1)))
				bucket['estHigh'] = bucket['High'].shift(1).rolling(4).max() + (abs(bucket['1DayApc'].shift(1)))
				bucket = bucket.query('longEMASlope >= ' + str(minActionableSlope) + ' and shortEMASlope >= ' + str(minActionableSlope)) #must filter after rolling calcuations
				bucket = bucket[['estLow','estHigh']]
				self.pricePredictions = bucket
					#+- correction or early down turn, loss of momentum
				bucket = self.historicalPrices.copy()
				bucket['estLow']  = bucket['Low'].shift(1).rolling(2).min() 
				bucket['estHigh'] = bucket['High'].shift(1).rolling(3).max()  * (1.005 + abs(bucket['shortEMASlope'].shift(1)))
				bucket = bucket.query('longEMASlope >= ' + str(minActionableSlope) + ' and shortEMASlope < -' + str(minActionableSlope))
				bucket = bucket[['estLow','estHigh']]
				self.pricePredictions = self.pricePredictions.append(bucket)
					 #-+ bounce or early recovery, loss of momentum
				bucket = self.historicalPrices.copy()
				bucket['estLow']  = bucket['Low'].shift(1)
				bucket['estHigh'] = bucket['High'].shift(1).rolling(3).max() * 1.02 
				bucket = bucket.query('longEMASlope < -' + str(minActionableSlope) + ' and shortEMASlope >= ' + str(minActionableSlope))
				bucket = bucket[['estLow','estHigh']]
					#-- Often over sold
				self.pricePredictions = self.pricePredictions.append(bucket)
				bucket = self.historicalPrices.copy() 
				bucket['estLow'] = bucket['Low'].shift(1).rolling(3).min() * .99
				bucket['estHigh'] = bucket['High'].shift(1).rolling(3).min() 
				bucket = bucket.query('longEMASlope < -' + str(minActionableSlope) + ' and shortEMASlope < -' + str(minActionableSlope))
				bucket = bucket[['estLow','estHigh']]
				self.pricePredictions = self.pricePredictions.append(bucket)
					#== no significant slope
				bucket = self.historicalPrices.copy() 
				bucket['estLow']  = bucket['Low'].shift(1).rolling(4).mean()
				bucket['estHigh'] = bucket['High'].shift(1).rolling(4).mean()
				bucket = bucket.query(str(minActionableSlope) + ' > longEMASlope >= -' + str(minActionableSlope) + ' or ' + str(minActionableSlope) + ' > shortEMASlope >= -' + str(minActionableSlope))
				bucket = bucket[['estLow','estHigh']]
				self.pricePredictions = self.pricePredictions.append(bucket)
				self.pricePredictions.sort_index(inplace=True)	
			d = self.historicalPrices.index[-1] 
			ls = self.historicalPrices['longEMASlope'][-1]
			ss = self.historicalPrices['shortEMASlope'][-1]
			deviation = self.historicalPrices['15DavDeviation'][-1]/2
			momentum = self.historicalPrices['3DayMomentum'][-1]/2 
			for i in range(0,daysIntoFuture): 	#Add new days to the end for crystal ball predictions
				momentum = (momentum + ls)/2 * (100+random.randint(-3,4))/100
				a = (self.pricePredictions['estLow'][-1] + self.pricePredictions['estHigh'][-1])/2
				if ls >= minActionableSlope and ss >= minActionableSlope: #++
					l = a * (1+momentum) + random.randint(round(-deviation*200),round(deviation*10))/100
					h = a * (1+momentum) + random.randint(round(-deviation*10),round(deviation*200))/100
				elif ls >= minActionableSlope and ss < -minActionableSlope: #+-
					l = a * (1+momentum) + random.randint(round(-deviation*200),round(deviation*10))/100
					h = a * (1+momentum) + random.randint(round(-deviation*10),round(deviation*400))/100
				elif ls < -minActionableSlope and ss >= minActionableSlope: #-+
					l = a * (1+momentum) + random.randint(round(-deviation*200),round(deviation*10))/100
					h = a * (1+momentum) + random.randint(round(-deviation*10),round(deviation*400))/100
				elif ls < -minActionableSlope and ss < -minActionableSlope: #--
					l = a * (1+momentum) + random.randint(round(-deviation*200),round(deviation*10))/100
					h = a * (1+momentum) + random.randint(round(-deviation*10),round(deviation*200))/100
				else:	#==
					l = a * (1+momentum) + random.randint(round(-deviation*200),round(deviation*10))/100
					h = a * (1+momentum) + random.randint(round(-deviation*10),round(deviation*200))/100
				self.pricePredictions.loc[d + BDay(i+1), 'estLow'] = l
				self.pricePredictions.loc[d + BDay(i+1), 'estHigh'] = h								
			self.pricePredictions['estAverage']	= (self.pricePredictions['estLow'] + self.pricePredictions['estHigh'])/2
		elif method==3:	#Use LSTM to predict prices
			from _classes.SeriesPrediction import StockPredictionNN
			temporarilyNormalize = False
			if not self.pricesNormalized:
				temporarilyNormalize = True
				self.NormalizePrices()
			model = StockPredictionNN(baseModelName='Prices', UseLSTM=True)
			FieldList = None
			#FieldList = BaseFieldList
			model.LoadSource(sourceDF=self.historicalPrices, FieldList=FieldList, window_size=1)
			model.LoadTarget(targetDF=None, prediction_target_days=daysIntoFuture)
			model.MakeBatches(batch_size=64, train_test_split=.93)
			model.BuildModel()
			if (not model.Load() and NNTrainingEpochs == 0): NNTrainingEpochs = 250
			if (NNTrainingEpochs > 0): 
				model.Train(epochs=NNTrainingEpochs)
				model.Save()
			model.Predict(True)
			self.pricePredictions = model.GetTrainingResults(False, False)
			self.pricePredictions = self.pricePredictions.rename(columns={'Average':'estAverage'})
			deviation = self.historicalPrices['15DavDeviation'][-1]/2
			self.pricePredictions['estLow'] = self.pricePredictions['estAverage'] * (1 - deviation)
			self.pricePredictions['estHigh'] = self.pricePredictions['estAverage'] * (1 + deviation)
			if temporarilyNormalize: 
				self.predictionsLoaded = True
				self.NormalizePrices()
		elif method==4:	#Use CNN to predict prices
			from _classes.SeriesPrediction import StockPredictionNN
			temporarilyNormalize = False
			if not self.pricesNormalized:
				temporarilyNormalize = True
				self.NormalizePrices()
			model = StockPredictionNN(baseModelName='Prices', UseLSTM=False)
			FieldList = BaseFieldList
			model.LoadSource(sourceDF=self.historicalPrices, FieldList=FieldList, window_size=daysIntoFuture*16)
			model.LoadTarget(targetDF=None, prediction_target_days=daysIntoFuture)
			model.MakeBatches(batch_size=64, train_test_split=.93)
			model.BuildModel()
			if (not model.Load() and NNTrainingEpochs == 0): NNTrainingEpochs = 250
			if (NNTrainingEpochs > 0): 
				model.Train(epochs=NNTrainingEpochs)
				model.Save()
			model.Predict(True)
			self.pricePredictions = model.GetTrainingResults(False, False)
			self.pricePredictions['estAverage'] = (self.pricePredictions['Low'] + self.pricePredictions['High'] + self.pricePredictions['Open'] + self.pricePredictions['Close'])/4
			deviation = self.historicalPrices['15DavDeviation'][-1]/2
			self.pricePredictions['estLow'] = self.pricePredictions['estAverage'] * (1 - deviation)
			self.pricePredictions['estHigh'] = self.pricePredictions['estAverage'] * (1 + deviation)
			self.pricePredictions = self.pricePredictions[['estLow','estAverage','estHigh']]
			if temporarilyNormalize: 
				self.predictionsLoaded = True
				self.NormalizePrices()
		self.pricePredictions.fillna(0, inplace=True)
		x = self.pricePredictions.join(self.historicalPrices)
		x['PercentageDeviation'] = abs((x['Average']-x['estAverage'])/x['Average'])
		self.predictionDeviation = x['PercentageDeviation'].tail(round(x.shape[0]/4)).mean() #Average of the last 25%, this is being kind as it includes some training data
		self.predictionsLoaded = True
		return True
	
	def PredictFuturePrice(self,fromDate:datetime, daysForward:int=1,method:int=1):
		fromDate=ToDateTime(fromDate)
		low,high,price,momentum,deviation = self.historicalPrices.loc[fromDate, ['Low','High','Average', '3DayMomentum','15DavDeviation']]
		#print(p,m,s)
		if method==0:
			futureLow = low
			futureHigh = high
		else:  
			futureLow = price * (1 + daysForward * momentum) - (price * deviation/2)
			futureHigh = price * (1 + daysForward * momentum) + (price * deviation/2)
		return futureLow, futureHigh	

	def GetDateFromIndex(self,indexLocation:int):
		if indexLocation >= self.historicalPrices.shape[0]: indexLocation = self.historicalPrices.shape[0]-1
		d = self.historicalPrices.index.values[indexLocation]
		return d

	def GetPrice(self,forDate:datetime, verbose:bool=False):
		forDate = ToDateTime(forDate)
		try:
			i = self.historicalPrices.index.get_loc(forDate, method='ffill')
			forDate = self.historicalPrices.index[i]
			r = self.historicalPrices.loc[forDate]['Average']
		except:
			if verbose: print('Unable to get price for ' + self.stockTicker + ' on ' + str(forDate))	
			r = 0
		return r
		
	def GetPriceSnapshot(self,forDate:datetime, verbose:bool=False):
		forDate = ToDateTime(forDate)
		sn = PriceSnapshot()
		sn.ticker = self.stockTicker
		sn.high, sn.low, sn.open,sn.close = 0,0,0,0
		try:
			i = self.historicalPrices.index.get_loc(forDate, method='ffill')
			forDate = self.historicalPrices.index[i]
		except:
			i = 0
			if verbose: print('Unable to get price snapshot for ' + self.stockTicker + ' on ' + str(forDate))	
		sn.snapShotDate = forDate 
		if i > 0:
			if not self.statsLoaded:
				sn.high,sn.low,sn.open,sn.close,sn.oneDayAverage =self.historicalPrices.loc[forDate,['High','Low','Open','Close','Average']]
			else:
				sn.high,sn.low,sn.open,sn.close,sn.oneDayAverage,sn.twoDayAverage,sn.fiveDayAverage,sn.shortEMA,sn.shortEMASlope,sn.longEMA,sn.longEMASlope,sn.channelHigh,sn.channelLow,sn.oneDayApc,sn.oneDayDeviation,sn.fiveDayDeviation,sn.fifteenDayDeviation,sn.dailyGain,sn.monthlyGain,sn.monthlyLossStd =self.historicalPrices.loc[forDate,['High','Low','Open','Close','Average','2DayAv','5DayAv','shortEMA','shortEMASlope','longEMA','longEMASlope','channelHigh', 'channelLow','1DayApc','1DayDeviation','5DavDeviation','15DavDeviation','dailyGain','monthlyGain','monthlyLossStd']]
				if sn.longEMASlope < 0:
					if sn.shortEMASlope > 0:	#bounce or early recovery
						sn.nextDayTarget = min(sn.oneDayAverage, sn.twoDayAverage)
					else:
						sn.nextDayTarget = min(sn.low, sn.twoDayAverage)			
				else:
					if sn.shortEMASlope < 0:	#correction or early downturn
						sn.nextDayTarget = max(sn.oneDayAverage, (sn.twoDayAverage*2)-sn.oneDayAverage) + (sn.oneDayAverage * (sn.longEMASlope))
					else:
						sn.nextDayTarget = max(sn.oneDayAverage, sn.twoDayAverage) + (sn.oneDayAverage * sn.longEMASlope)
					#sn.nextDayTarget = max(sn.oneDayAverage, sn.twoDayAverage) + (sn.oneDayAverage * sn.longEMASlope)
				if not self.predictionsLoaded or forDate >= self.historyEndDate:
					sn.estLow,sn.estHigh= self.PredictFuturePrice(forDate,1)
				else:
					tomorrow =  forDate.date() + timedelta(days=1) 
					sn.estLow,sn.estHigh= self.pricePredictions.loc[tomorrow,['estLow','estHigh']]
		return sn

	def GetCurrentPriceSnapshot(self): return self.GetPriceSnapshot(self.historyEndDate)

	def GetPriceHistory(self, fieldList:list = None, includePredictions:bool = False):
		if fieldList == None:
			r = self.historicalPrices.copy() #best to pass back copies instead of reference.
		else:
			r = self.historicalPrices[fieldList].copy() #best to pass back copies instead of reference.			
		if includePredictions: r = r.join(self.pricePredictions, how='outer')
		return r
		
	def GetPricePredictions(self):
		return self.pricePredictions.copy()  #best to pass back copies instead of reference.

	def GraphData(self, endDate:datetime=None, daysToGraph:int=90, graphTitle:str=None, includePredictions:bool=False, saveToFile:bool=False, fileNameSuffix:str=None, saveToFolder:str='', dpi:int=600, trimHistoricalPredictions:bool = True):
		PlotSetDefaults()
		if not self.statsLoaded: self.CalculateStats()
		if includePredictions:
			if not self.predictionsLoaded: self.PredictPrices()
			if endDate == None: endDate = self.pricePredictions.index.max()
			endDate = ToDateTime(endDate)
			startDate = endDate - BDay(daysToGraph) 
			fieldSet = ['High','Low', 'channelHigh', 'channelLow', 'estHigh','estLow', 'shortEMA','longEMA']
			if trimHistoricalPredictions: 
				y = self.pricePredictions[self.pricePredictions.index >= self.historyEndDate]
				x = self.historicalPrices.join(y, how='outer')
			else: 
				fieldSet = ['High','Low', 'estHigh','estLow']
				x = self.historicalPrices.join(self.pricePredictions, how='outer')
			if daysToGraph > 1800:	fieldSet = ['Average', 'estHigh','estLow']
		else:
			if endDate == None: endDate = self.historyEndDate
			endDate = ToDateTime(endDate)
			startDate = endDate - BDay(daysToGraph) 
			fieldSet = ['High','Low', 'channelHigh', 'channelLow','shortEMA','longEMA']
			if daysToGraph > 1800: fieldSet = ['Average']
			x = self.historicalPrices
		if fileNameSuffix == None: fileNameSuffix = str(endDate)[:10] + '_' + str(daysToGraph) + 'days'
		if graphTitle==None: graphTitle = self.stockTicker + ' ' + fileNameSuffix
		x = x[(x.index >= startDate) & (x.index <= endDate)]
		if x.shape[0] == 0:
			print('Empty source data')
		else:
			ax=x.loc[startDate:endDate,fieldSet].plot(title=graphTitle, linewidth=.75, color = ['blue', 'red','purple','purple','mediumseagreen','seagreen'])			
			ax.set_xlabel('Date')
			ax.set_ylabel('Price')
			ax.tick_params(axis='x', rotation=70)
			ax.grid(b=True, which='major', color='black', linestyle='solid', linewidth=.5)
			ax.grid(b=True, which='minor', color='0.65', linestyle='solid', linewidth=.1)
			PlotScalerDateAdjust(startDate, endDate, ax)
			if saveToFile:
				if not fileNameSuffix =='': fileNameSuffix = '_' + fileNameSuffix
				if saveToFolder=='': saveToFolder = self._dataFolderCharts
				if not saveToFolder.endswith('/'): saveToFolder = saveToFolder + '/'
				if CreateFolder(saveToFolder): 	plt.savefig(saveToFolder + self.stockTicker + fileNameSuffix + '.png', dpi=dpi)
				print(' Saved to ' + saveToFolder + self.stockTicker + fileNameSuffix + '.png')
			else:
				plt.show()
			plt.close('all')

class Tranche: #interface for handling actions on a chunk of funds
	ticker = ''
	size = 0
	units = 0
	available = True
	purchased = False
	marketOrder = False
	sold = False
	expired = False
	dateBuyOrderPlaced = None
	dateBuyOrderFilled = None
	dateSellOrderPlaced = None
	dateSellOrderFilled = None
	buyOrderPrice = 0
	purchasePrice = 0
	sellOrderPrice = 0
	sellPrice = 0
	latestPrice = 0
	expireAfterDays = 0
	_verbose = False
	
	def __init__(self, size:int=1000):
		self.size = size
		
	def AdjustBuyUnits(self, newValue:int):	
		if self._verbose: print(' Adjusting Buy from ' + str(self.units) + ' to ' + str(newValue) + ' units (' + self.ticker + ')')
		self.units=newValue

	def CancelOrder(self, verbose:bool=False): 
		self.marketOrder=False
		self.expireAfterDays=0
		if self.purchased:
			if verbose: print(' Sell order on ', self.ticker, ' canceled.')
			self.dateSellOrderPlaced = None
			self.sellOrderPrice = 0
			self.expired=False
		else:
			if verbose: print(' Buy order for ', self.ticker, ' canceled.')
			self.Recycle()
		
	def Expire(self):
		if not self.purchased:  #cancel buy
			if self._verbose: print(' Buy order from ' + str(self.dateBuyOrderPlaced) + ' has expired (' + self.ticker + ')')
			self.Recycle()
		else: #cancel sell
			if self._verbose: print(' Sell order from ' + str(self.dateSellOrderPlaced) + ' has expired (' + self.ticker + ')')
			self.dateSellOrderPlaced=None
			self.sellOrderPrice=0
			self.marketOrder = False
			self.expireAfterDays = 0
			self.expired=False

	def PlaceBuy(self, ticker:str, price:float, datePlaced:datetime, marketOrder:bool=False, expireAfterDays:int=10, verbose:bool=False):
		#returns amount taken out of circulation by the order
		r = 0
		self._verbose = verbose
		if self.available and price > 0:
			self.available = False
			self.ticker=ticker
			self.marketOrder = marketOrder
			self.dateBuyOrderPlaced = datePlaced
			self.buyOrderPrice=price
			self.units = floor(self.size/price)
			self.purchased = False
			self.expireAfterDays=expireAfterDays
			r=(price*self.units)
			if self._verbose: 
				if marketOrder:
					print(datePlaced, ' Buy placed at Market (' + str(price) + ') for ' + str(self.units) + ' Cost ' + str(r) + '(' + self.ticker + ')')
				else:
					print(datePlaced, ' Buy placed at ' + str(price) + ' for ' + str(self.units) + ' Cost ' + str(r) + '(' + self.ticker + ')')
		return r
		
	def PlaceSell(self, price, datePlaced, marketOrder:bool=False, expireAfterDays:int=10, verbose:bool=False):
		r = False
		self._verbose = verbose
		if self.purchased and price > 0:
			self.sold = False
			self.dateSellOrderPlaced = datePlaced
			self.sellOrderPrice = price
			self.marketOrder = marketOrder
			self.expireAfterDays=expireAfterDays
			if self._verbose: 
				if marketOrder: 
					print(datePlaced, ' Sell placed at Market for ' + str(self.units) + ' (' + self.ticker + ')')
				else:
					print(datePlaced, ' Sell placed at ' + str(price) + ' for ' + str(self.units) + ' (' + self.ticker + ')')
			r=True
		return r

	def PrintDetails(self):
		if not self.ticker =='' or True:
			print("Stock: " + self.ticker)
			print("units: " + str(self.units))
			print("available: " + str(self.available))
			print("purchased: " + str(self.purchased))
			print("dateBuyOrderPlaced: " + str(self.dateBuyOrderPlaced))
			print("dateBuyOrderFilled: " + str(self.dateBuyOrderFilled))
			print("buyOrderPrice: " + str(self.buyOrderPrice))
			print("purchasePrice: " + str(self.purchasePrice))
			print("dateSellOrderPlaced: " + str(self.dateSellOrderPlaced))
			print("dateSellOrderFilled: " + str(self.dateSellOrderFilled))
			print("sellOrderPrice: " + str(self.sellOrderPrice))
			print("sellPrice: " + str(self.sellPrice))
			print("latestPrice: " + str(self.latestPrice))
			print("\n")

	def Recycle(self):
		self.ticker = ""
		self.units = 0
		self.available = True
		self.purchased = False
		self.sold = False
		self.expired = False
		self.marketOrder = False
		self.dateBuyOrderPlaced = None
		self.dateBuyOrderFilled = None
		self.dateSellOrderPlaced = None
		self.dateSellOrderFilled = None
		self.latestPrice=None
		self.buyOrderPrice = 0
		self.purchasePrice = 0
		self.sellOrderPrice = 0
		self.sellPrice = 0
		self.expireAfterDays = 0
		self._verbose=False
	
	def UpdateStatus(self, price, dateChecked):
		#Returns True if the order had action: filled or expired.
		r = False
		if price > 0: 
			self.latestPrice = price
			if self.buyOrderPrice > 0 and not self.purchased:
				if self.buyOrderPrice >= price or self.marketOrder:
					self.dateBuyOrderFilled = dateChecked
					self.purchasePrice = price
					self.purchased=True
					if self._verbose: print(dateChecked, ' Buy ordered on ' + str(self.dateBuyOrderPlaced) + ' filled for ' + str(price) + ' (' + self.ticker + ')')
					r=True
				else:
					self.expired = (DateDiffDays(self.dateBuyOrderPlaced , dateChecked) > self.expireAfterDays)
					if self.expired and self._verbose: print(dateChecked, 'Buy order from ' + str(self.dateBuyOrderPlaced) + ' expired.')
					r = self.expired
			elif self.sellOrderPrice > 0 and not self.sold:
				if self.sellOrderPrice <= price or self.marketOrder:
					self.dateSellOrderFilled = dateChecked
					self.sellPrice = price
					self.sold=True
					self.expired=False
					if self._verbose: print(dateChecked, ' Sell ordered on ' + str(self.dateSellOrderPlaced) + ' filled for ' + str(price) + ' (' + self.ticker + ')') 
					r=True
				else:
					self.expired = (DateDiffDays(self.dateSellOrderPlaced, dateChecked) > self.expireAfterDays)
					if self.expired and self._verbose: print(dateChecked, 'Sell order from ' + str(self.dateSellOrderPlaced) + ' expired.')
					r = self.expired
			else:
				r=False
		return r

class Position:	#Simple interface for open positions
	def __init__(self, t:Tranche):
		self._t = t
		self.ticker = t.ticker
	def CancelSell(self): 
		if self._t.purchased: self._t.CancelOrder(verbose=True)
	def CurrentValue(self): return self._t.units * self._t.latestPrice
	def Sell(self, price:float, datePlaced:datetime, marketOrder:bool=False, expireAfterDays:int=90): self._t.PlaceSell(price=price, datePlaced=datePlaced, marketOrder=marketOrder, expireAfterDays=expireAfterDays, verbose=True)
	def SellPending(self): return (self._t.sellOrderPrice >0) and not (self._t.sold or  self._t.expired)
	def LatestPrice(self): return self._t.latestPrice
	
class Portfolio:
	portfolioName = ''
	tradeHistory = [] #DataFrame of trades.  Note: though you can trade more than once a day it is only going to keep one entry per day per stock
	dailyValue = []	  #DataFrame for the value at the end of each day
	_cash=0
	_fundsCommittedToOrders=0
	_commisionCost = 0
	_tranches = []			#Sets of funds for investing, rather than just a pool of cash.  Simplifies accounting.
	_tranchCount = 0
	_verbose = False
	
	def __del__(self):
		self._cash = 0
		self._tranches = None

	def __init__(self, portfolioName:str, startDate:datetime, totalFunds:int=10000, tranchSize:int=1000, trackHistory:bool=True, verbose:bool=True):
		self.portfolioName = portfolioName
		self._cash = totalFunds
		self._fundsCommittedToOrders = 0
		self._verbose = verbose
		self._tranchCount = floor(totalFunds/tranchSize)
		self._tranches = [Tranche(tranchSize) for x in range(self._tranchCount)]
		self.dailyValue = pd.DataFrame([[startDate,totalFunds,0,totalFunds]], columns=list(['Date','CashValue','AssetValue','TotalValue']))
		self.dailyValue.set_index(['Date'], inplace=True)
		self.trackHistory = trackHistory
		if trackHistory: 
			self.tradeHistory = pd.DataFrame(columns=['dateBuyOrderPlaced','ticker','dateBuyOrderFilled','dateSellOrderPlaced','dateSellOrderFilled','units','buyOrderPrice','purchasePrice','sellOrderPrice','sellPrice','NetChange'])
			self.tradeHistory.set_index(['dateBuyOrderPlaced','ticker'], inplace=True)

	#----------------------  Status and position info  ---------------------------------------
	def AccountingError(self):
		r = False
		if not self.ValidateFundsCommittedToOrders() == 0: 
			print(' Accounting error: inaccurcy in funds committed to orders!')
			r=True
		if self.FundsAvailable() + self._tranchCount*self._commisionCost < -10: #Over-committed funds		
			OrdersAdjusted = False		
			for t in self._tranches:
				if not t.purchased and t.units > 0:
					print(' Reducing purchase of ' + t.ticker + ' by one unit due to overcommitted funds.')
					t.units -= 1
					OrdersAdjusted = True
					break
			if OrdersAdjusted: self.ValidateFundsCommittedToOrders(True)
			if self.FundsAvailable() + self._tranchCount*self._commisionCost < -10: 
				OrdersAdjusted = False		
				for t in self._tranches:
					if not t.purchased and t.units > 1:
						print(' Reducing purchase of ' + t.ticker + ' by two units due to overcommitted funds.')
						t.units -= 2
						OrdersAdjusted = True
						break
			if self.FundsAvailable() + self._tranchCount*self._commisionCost < -10: #Over-committed funds						
				print(' Accounting error: negative cash balance.  (Cash, CommittedFunds, AvailableFunds) ', self._cash, self._fundsCommittedToOrders, self.FundsAvailable())
				r=True
		return r

	def FundsAvailable(self): return (self._cash - self._fundsCommittedToOrders)
	
	def PendingOrders(self):
		a, b, s, l = self.PositionSummary()
		return (b+s > 0)

	def GetPositions(self, ticker:str='', asDataFrame:bool=False):	#returns reference to the tranche of active positions or a dataframe with counts
		r = []
		for t in self._tranches:
			if t.purchased and (t.ticker==ticker or ticker==''): 
				p = Position(t)
				r.append(p)
		if asDataFrame:
			y=[]
			for x in r: y.append(x.ticker)
			r = pd.DataFrame(y,columns=list(['Ticker']))
			r = r.groupby(['Ticker']).size().reset_index(name='CurrentHoldings')
			r.set_index(['Ticker'], inplace=True)
		return r

	def PositionSummary(self):
		available=0
		buyPending=0
		sellPending=0
		longPostition = 0
		for t in self._tranches:
			if t.available:
				available +=1
			elif not t.purchased:
				buyPending +=1
			elif t.purchased and t.dateSellOrderPlaced==None:
				longPostition +=1
			elif t.dateSellOrderPlaced:
				sellPending +=1
		return available, buyPending, sellPending, longPostition			

	def PrintPositions(self):
		i=0
		for t in self._tranches:
			if not t.ticker =='' or True:
				print('Set: ' + str(i))
				t.PrintDetails()
			i=i+1
		print('Funds committed to orders: ' + str(self._fundsCommittedToOrders))
		print('available funds: ' + str(self._cash - self._fundsCommittedToOrders))

	def TranchesAvailable(self):
		a, b, s, l = self.PositionSummary()
		return a

	def ValidateFundsCommittedToOrders(self, SaveAdjustments:bool=True):
		#Returns difference between recorded value and actual
		x=0
		for t in self._tranches:
			if not t.available and not t.purchased: 
				x = x + (t.units*t.buyOrderPrice) + self._commisionCost
		if round(self._fundsCommittedToOrders, 5) == round(x,5): self._fundsCommittedToOrders=x
		if not (self._fundsCommittedToOrders - x) ==0:
			if SaveAdjustments: 
				self._fundsCommittedToOrders = x
			else:
				print( 'Committed funds variance actual/recorded', x, self._fundsCommittedToOrders)
		return (self._fundsCommittedToOrders - x)

	def Value(self):
		assetValue=0
		for t in self._tranches:
			if t.purchased:
				assetValue = assetValue + (t.units*t.latestPrice)
		return self._cash, assetValue
		
	def ReEvaluateTrancheCount(self, verbose:bool=False):
		#Portfolio performance may require adjusting the available Tranches
		tranchSize = self._tranches[0].size
		c = self._tranchCount
		availableTranches,_,_,_ = self.PositionSummary()
		availableFunds = self._cash - self._fundsCommittedToOrders
		targetAvailable = int(availableFunds/tranchSize)
		if targetAvailable > availableTranches:
			if verbose: 
				print(' Available Funds: ', availableFunds, availableTranches * tranchSize)
				print(' Adding ' + str(targetAvailable - availableTranches) + ' new Tranches to portfolio..')
			for i in range(targetAvailable - availableTranches):
				self._tranches.append(Tranche(tranchSize))
				self._tranchCount +=1
		elif targetAvailable < availableTranches:
			if verbose: print( 'Removing ' + str(availableTranches - targetAvailable) + ' tranches from portfolio..')
			#print(targetAvailable, availableFunds, tranchSize, availableTranches)
			i = self._tranchCount-1
			while i > 0:
				if self._tranches[i].available and targetAvailable < availableTranches:
					if verbose: 
						print(' Available Funds: ', availableFunds, availableTranches * tranchSize)
						print(' Removing tranch at ', i)
					self._tranches.pop(i)	#remove last available
					self._tranchCount -=1
					availableTranches -=1
				i -=1


	#--------------------------------------  Order interface  ---------------------------------------
	def CancelAllOrders(self, currentDate:datetime):
		for t in self._tranches:
			t.CancelOrder()
		#for t in self._tranches:						self.CheckOrders(t.ticker, t.latestPrice, currentDate) 

	def PlaceBuy(self, ticker:str, price:float, datePlaced:datetime, marketOrder:bool=False, expireAfterDays:int=10, verbose:bool=False):
		#Place with first available tranch, returns True if order was placed
		r=False
		price = round(price, 3)
		oldestExistingOrder = None
		availableCash = self.FundsAvailable()
		units=0
		if price > 0: units = int(self._tranches[0].size/price)
		cost = units*price + self._commisionCost
		if availableCash < cost and units > 2:
			units -=1
			cost = units*price + self._commisionCost
		if units == 0 or availableCash < cost:
			if verbose: 
				if price==0:
					print( 'Unable to purchase ' + ticker + '.  Price lookup failed.')
				else:
					print( 'Unable to purchase ' + ticker + '.  Price (' + str(price) + ') exceeds available funds', availableCash)
		else:	
			for t in self._tranches: #Find available 
				if t.available :	#Place new order
					self._fundsCommittedToOrders = self._fundsCommittedToOrders + cost 
					x = self._commisionCost + t.PlaceBuy(ticker=ticker, price=price, datePlaced=datePlaced, marketOrder=marketOrder, expireAfterDays=expireAfterDays, verbose=verbose) 
					if not x == cost: #insufficient funds for full purchase
						if verbose: print(' Expected cost changed from', cost, 'to', x)
						self._fundsCommittedToOrders = self._fundsCommittedToOrders - cost + x + self._commisionCost
					r=True
					break
				elif not t.purchased and t.ticker == ticker:	#Might have to replace existing order
					if oldestExistingOrder == None:
						oldestExistingOrder=t.dateBuyOrderPlaced
					else:
						if oldestExistingOrder > t.dateBuyOrderPlaced: oldestExistingOrder=t.dateBuyOrderPlaced
		if not r and units > 0 and False:	#We could allow replacing oldest existing order
			if oldestExistingOrder == None:
				if self.TranchesAvailable() > 0:
					if verbose: print(' Unable to buy ' + str(units) + ' of ' + ticker + ' with funds available: ' + str(FundsAvailable))
				else: 
					if verbose: print(' Unable to buy ' + ticker + ' no tranches available')
			else:
				for t in self._tranches:
					if not t.purchased and t.ticker == ticker and oldestExistingOrder==t.dateBuyOrderPlaced:
						if verbose: print(' No tranch available... replacing order from ' + str(oldestExistingOrder))
						oldCost = t.buyOrderPrice * t.units + self._commisionCost
						if verbose: print(' Replacing Buy order for ' + ticker + ' from ' + str(t.buyOrderPrice) + ' to ' + str(price))
						t.units = units
						t.buyOrderPrice = price
						t.dateBuyOrderPlaced = datePlaced
						t.marketOrder = marketOrder
						self._fundsCommittedToOrders = self._fundsCommittedToOrders - oldCost + cost 
						r=True
						break		
		return r

	def PlaceSell(self, ticker:str, price:float, datePlaced:datetime, marketOrder:bool=False, expireAfterDays:int=10, datepurchased:datetime=None, verbose:bool=False):
		#Returns True if order was placed
		r=False
		price = round(price, 3)
		for t in self._tranches:
			if t.ticker == ticker and t.purchased and t.sellOrderPrice==0 and (datepurchased is None or t.dateBuyOrderFilled == datepurchased):
				t.PlaceSell(price=price, datePlaced=datePlaced, marketOrder=marketOrder, expireAfterDays=expireAfterDays, verbose=verbose)
				r=True
				break
		if not r:	#couldn't find one without a sell, try to update an existing sell order
			for t in self._tranches:
				if t.ticker == ticker and t.purchased:
					if verbose: print(' Updating existing sell order ')
					t.PlaceSell(price=price, datePlaced=datePlaced, marketOrder=marketOrder, expireAfterDays=expireAfterDays, verbose=verbose)
					r=True
					break					
		return r

	def SellAllPositions(self, datePlaced:datetime, ticker:str='', verbose:bool=False):
		for t in self._tranches:
			if t.purchased and (t.ticker==ticker or ticker==''): 
				t.PlaceSell(price=t.latestPrice, datePlaced=datePlaced, marketOrder=True, expireAfterDays=5, verbose=verbose)
		self.ProcessDay(withIncrement=False)

	#--------------------------------------  Order Processing ---------------------------------------
	def _CheckOrders(self, ticker, price, dateChecked):
		#check if there was action on any pending orders and update current price of tranche
		price = round(price, 3)
		for t in self._tranches:
			if t.ticker == ticker:
				r = t.UpdateStatus(price, dateChecked)
				if r:	#Order was filled, update account
					if t.expired:
						if self._verbose: print(t.ticker, " expired ")
						if not t.purchased: 
							self._fundsCommittedToOrders -= (t.units*t.buyOrderPrice)	#return funds committed to order
							self._fundsCommittedToOrders -= self._commisionCost
						t.Expire()
					elif t.sold:
						if self._verbose: print(t.ticker, " sold for ",t.sellPrice)
						self._cash = self._cash + (t.units*t.sellPrice) - self._commisionCost
						if self._verbose and self._commisionCost > 0: print(' Commission charged for Sell: ' + str(self._commisionCost))
						if self.trackHistory:
							self.tradeHistory.loc[(t.dateBuyOrderPlaced, t.ticker)]=[t.dateBuyOrderFilled,t.dateSellOrderPlaced,t.dateSellOrderFilled,t.units,t.buyOrderPrice,t.purchasePrice,t.sellOrderPrice,t.sellPrice,((t.sellPrice - t.purchasePrice)*t.units)-self._commisionCost*2] 
						t.Recycle()
					elif t.purchased:
						self._fundsCommittedToOrders -= (t.units*t.buyOrderPrice)	#return funds committed to order
						self._fundsCommittedToOrders -= self._commisionCost
						fundsavailable = self._cash - abs(self._fundsCommittedToOrders)
						if t.marketOrder:
							actualCost = t.units*price
							if self._verbose: print(t.ticker, " purchased for ",price)
							if (fundsavailable - actualCost - self._commisionCost) < 25:	#insufficient funds
								unitsCanAfford = max(floor((fundsavailable - self._commisionCost)/price)-1, 0)
								if self._verbose:
									print(' Ajusting units on market order for ' + ticker + ' Price: ', price, ' Requested Units: ', t.units,  ' Can afford:', unitsCanAfford)
									print(' Cash: ', self._cash, ' Committed Funds: ', self._fundsCommittedToOrders, ' Available: ', fundsavailable)
								if unitsCanAfford ==0:
									t.Recycle()
								else:
									t.AdjustBuyUnits(unitsCanAfford)
						if t.units == 0:
							if self._verbose: print( 'Can not afford any ' + ticker + ' at market ' + str(price) + ' canceling Buy')
							t.Recycle()
						else:
							self._cash = self._cash - (t.units*price) - self._commisionCost 
							if self._verbose and self._commisionCost > 0: print(' Commission charged for Buy: ' + str(self._commisionCost))		
							if self.trackHistory:							
								self.tradeHistory.loc[(t.dateBuyOrderPlaced,t.ticker), 'dateBuyOrderFilled']=t.dateBuyOrderFilled #Create the row
								self.tradeHistory.loc[(t.dateBuyOrderPlaced,t.ticker)]=[t.dateBuyOrderFilled,t.dateSellOrderPlaced,t.dateSellOrderFilled,t.units,t.buyOrderPrice,t.purchasePrice,t.sellOrderPrice,t.sellPrice,''] 
						
	def _CheckPriceSequence(self, ticker, p1, p2, dateChecked):
		#approximate a price sequence between given prices
		steps=40
		if p1==p2:
			self._CheckOrders(ticker, p1, dateChecked)		
		else:
			step = (p2-p1)/steps
			for i in range(steps):
				p = round(p1 + i * step, 3)
				self._CheckOrders(ticker, p, dateChecked)
			self._CheckOrders(ticker, p2, dateChecked)	

	def ProcessDaysOrders(self, ticker, open, high, low, close, dateChecked):
		#approximate a sequence of the day's prices for given ticker, check orders for each, update price value
		if self.PendingOrders() > 0:
			p2=low
			p3=high
			if (high - open) < (open - low):
				p2=high
				p3=low
			#print(' Given price sequence      ' + str(open) + ' ' + str(high) + ' ' + str(low) + ' ' + str(close))
			#print(' Estimating price sequence ' + str(open) + ' ' + str(p2) + ' ' + str(p3) + ' ' + str(close))
			self._CheckPriceSequence(ticker, open, p2, dateChecked)
			self._CheckPriceSequence(ticker, p2, p3, dateChecked)
			self._CheckPriceSequence(ticker, p3, close, dateChecked)
		else:
			self._CheckOrders(ticker, close, dateChecked)	#No open orders but still need to update last prices
		self.ValidateFundsCommittedToOrders(True)
		_cashValue, assetValue = self.Value()
		self.dailyValue.loc[dateChecked]=[_cashValue,assetValue,_cashValue + assetValue] 

	#--------------------------------------  Closing Reporting ---------------------------------------
	def SaveTradeHistoryToFile(self, foldername:str, addTimeStamp:bool = False):
		if CreateFolder(foldername):
			filePath = foldername + self.portfolioName 
			if addTimeStamp: filePath += '_' + GetDateTimeStamp()
			filePath += '_trades.csv'
			if self.trackHistory:
				self.tradeHistory.to_csv(filePath)

	def SaveDailyValueToFile(self, foldername:str, addTimeStamp:bool = False):
		if CreateFolder(foldername):
			filePath = foldername + self.portfolioName 
			if addTimeStamp: filePath += '_' + GetDateTimeStamp()
			filePath+= '_dailyvalue.csv'
			self.dailyValue.to_csv(filePath)
		
class TradingModel(Portfolio):
	#Extends Portfolio to trading environment for testing models
	modelName = None
	modelStartDate  = None	
	modelEndDate = None
	modelReady = False
	currentDate = None
	priceHistory = []  #list of price histories for each stock in _stockTickerList
	startingValue = 0 
	verbose = False
	_stockTickerList = []	#list of stocks currently held
	_dataFolderTradeModel = 'data/trademodel/'
	Custom1 = None	#can be used to store custom values when using the model
	Custom2 = None
	_NormalizePrices = False

	def __init__(self, modelName:str, startingTicker:str, startDate:datetime, durationInYears:int, totalFunds:int, tranchSize:int=1000,verbose:bool=False, trackHistory:bool=True):
		#pricesAsPercentages:bool=False would be good but often results in Nan values
		#expects date format in local format, from there everything will be converted to database format				
		startDate = ToDateTime(startDate)
		endDate = startDate + timedelta(days=365 * durationInYears)
		self.modelReady = False
		CreateFolder(self._dataFolderTradeModel)
		p = PricingData(startingTicker)
		if p.LoadHistory(requestedStartDate=startDate, requestedEndDate=endDate, verbose=verbose): 
			if verbose: print(' Loading ' + startingTicker)
			p.CalculateStats()
			p.TrimToDateRange(startDate - timedelta(days=60), endDate + timedelta(days=10))
			self.priceHistory = [p]
			i = p.historicalPrices.index.get_loc(startDate, method='nearest')
			startDate = p.historicalPrices.index[i]
			i = p.historicalPrices.index.get_loc(endDate, method='nearest')
			endDate = p.historicalPrices.index[i]
			if not PandaIsInIndex(p.historicalPrices, startDate): startDate += timedelta(days=1)
			if not PandaIsInIndex(p.historicalPrices, startDate): startDate += timedelta(days=1)
			if not PandaIsInIndex(p.historicalPrices, startDate): startDate += timedelta(days=1)
			if not PandaIsInIndex(p.historicalPrices, endDate): endDate -= timedelta(days=1)
			if not PandaIsInIndex(p.historicalPrices, endDate): endDate -= timedelta(days=1)
			if not PandaIsInIndex(p.historicalPrices, endDate): endDate -= timedelta(days=1)
			self.modelStartDate = startDate
			self.modelEndDate = endDate
			self.currentDate = self.modelStartDate
			modelName += '_' + str(startDate)[:10] + '_' + str(durationInYears) + 'year'
			self.modelName = modelName
			super
			self._stockTickerList = [startingTicker]
			self.startingValue = totalFunds
			self.modelReady = not(pd.isnull(self.modelStartDate))
		super(TradingModel, self).__init__(portfolioName=modelName, startDate=startDate, totalFunds=totalFunds, tranchSize=tranchSize, trackHistory=trackHistory, verbose=verbose)
		
	def __del__(self):
		self._stockTickerList = None
		del self.priceHistory[:] 
		self.priceHistory = None
		self.modelStartDate  = None	
		self.modelEndDate = None
		self.modelReady = False

	def AddStockTicker(self, ticker:str):
		r = False
		if not ticker in self._stockTickerList:
			p = PricingData(ticker)
			if self.verbose: print(' Loading price history for ' + ticker)
			if p.LoadHistory(requestedStartDate=self.modelStartDate, requestedEndDate=self.modelEndDate): 
				p.CalculateStats()
				p.TrimToDateRange(self.modelStartDate - timedelta(days=60), self.modelEndDate + timedelta(days=10))
				if len(p.historicalPrices) > len(self.priceHistory[0].historicalPrices): #first element is used for trading day indexing, replace if this is a better match
					self.priceHistory.insert(0, p)
					self._stockTickerList.insert(0, ticker)
				else:
					self.priceHistory.append(p)
					self._stockTickerList.append(ticker)
				r = True
			else:
				print( 'Unable to download price history for ticker ' + ticker)
		return r

	def CancelAllOrders(self): super(TradingModel, self).CancelAllOrders(self.currentDate)
	
	def CloseModel(self, plotResults:bool=True, saveHistoryToFile:bool=True, folderName:str='data/trademodel/', dpi:int=600):	
		cashValue, assetValue = self.Value()
		if assetValue > 0:
			self.SellAllPositions(self.currentDate)
		cashValue, assetValue = self.Value()
		netChange = cashValue + assetValue - self.startingValue 		
		if saveHistoryToFile:
			self.SaveDailyValueToFile(folderName)
			self.SaveTradeHistoryToFile(folderName)
		print('Model ' + self.modelName + ' from ' + str(self.modelStartDate)[:10] + ' to ' + str(self.modelEndDate)[:10])
		print('Cash: ' + str(round(cashValue)) + ' asset: ' + str(round(assetValue)) + ' total: ' + str(round(cashValue + assetValue)))
		print('Net change: ' + str(round(netChange)), str(round((netChange/self.startingValue) * 100, 2)) + '%')
		print('')
		if plotResults and self.trackHistory: 
			self.PlotTradeHistoryAgainstHistoricalPrices(self.tradeHistory, self.priceHistory[0].GetPriceHistory(), self.modelName)
		return cashValue + assetValue
		
	def CalculateGain(self, startDate:datetime, endDate:datetime):
		try:
			startValue = self.dailyValue['TotalValue'].at[startDate]
			endValue = self.dailyValue['TotalValue'].at[endDate]
			gain = endValue = startValue
			percentageGain = endValue/startValue
		except:
			gain = -1
			percentageGain = -1
			print('Unable to calculate gain for ', startDate, endDate)
		return gain, percentageGain
			
	def GetCustomValues(self): return self.Custom1, self.Custom2
	def GetDailyValue(self): return self.dailyValue #returns dataframe with daily value of portfolio
	def GetValueAt(self, date): 
		try:
			i = self.dailyValue.index.get_loc(date, method='nearest')
			r = self.dailyValue.iloc[i]['TotalValue']
		except:
			print('Unable to return value at ', date)
			r=-1
		return r

	def GetPrice(self, ticker:str=''): 
		#returns snapshot object of yesterday's pricing info to help make decisions today
		forDate = self.currentDate + timedelta(days=-1)
		r = None
		if ticker =='':
			r = self.priceHistory[0].GetPrice(forDate)
		else:
			if not ticker in self._stockTickerList:	self.AddStockTicker(ticker)
			if ticker in self._stockTickerList:
				for ph in self.priceHistory:
					if ph.stockTicker == ticker: r = ph.GetPrice(forDate) 
		return r

	def GetPriceSnapshot(self, ticker:str=''): 
		#returns snapshot object of yesterday's pricing info to help make decisions today
		forDate = self.currentDate + timedelta(days=-1)
		r = None
		if ticker =='':
			r = self.priceHistory[0].GetPriceSnapshot(forDate)
		else:
			if not ticker in self._stockTickerList:	self.AddStockTicker(ticker)
			if ticker in self._stockTickerList:
				for ph in self.priceHistory:
					if ph.stockTicker == ticker: r = ph.GetPriceSnapshot(forDate) 
		return r

	def ModelCompleted(self):
		if self.currentDate ==None or self.modelEndDate == None: 
			r = True
			print('Model start or end date is None', self.currentDate, self.modelEndDate)
		else:
			r = self.currentDate >= self.modelEndDate
		return(r)

	def NormalizePrices(self):
		self._NormalizePrices =  not self._NormalizePrices
		for p in self.priceHistory:
			if not p.pricesNormalized: p.NormalizePrices()
		
	def PlaceBuy(self, ticker:str, price:float, marketOrder:bool=False, expireAfterDays:bool=10, verbose:bool=False):
		if not ticker in self._stockTickerList: self.AddStockTicker(ticker)	
		if ticker in self._stockTickerList:	
			if marketOrder: price = self.GetPrice(ticker)
			super(TradingModel, self).PlaceBuy(ticker, price, self.currentDate, marketOrder, expireAfterDays, verbose)
		else:
			print(' Unable to add ticker ' + ticker + ' to portfolio.')

	def PlaceSell(self, ticker:str, price:float, marketOrder:bool=False, expireAfterDays:bool=10, datepurchased:datetime=None, verbose:bool=False): 
		super(TradingModel, self).PlaceSell(ticker=ticker, price=price, datePlaced=self.currentDate, marketOrder=marketOrder, expireAfterDays=expireAfterDays, verbose=verbose)

	def PlotTradeHistoryAgainstHistoricalPrices(self, tradeHist:pd.DataFrame, priceHist:pd.DataFrame, modelName:str):
		buys = tradeHist.loc[:,['dateBuyOrderFilled','purchasePrice']]
		buys = buys.rename(columns={'dateBuyOrderFilled':'Date'})
		buys.set_index(['Date'], inplace=True)
		sells  = tradeHist.loc[:,['dateSellOrderFilled','sellPrice']]
		sells = sells.rename(columns={'dateSellOrderFilled':'Date'})
		sells.set_index(['Date'], inplace=True)
		dfTemp = priceHist.loc[:,['High','Low', 'channelHigh', 'channelLow']]
		dfTemp = dfTemp.join(buys)
		dfTemp = dfTemp.join(sells)
		PlotDataFrame(dfTemp, modelName, 'Date', 'Value')

	def ProcessDay(self, withIncrement:bool=True):
		#Process current day and increment the current date
		if self.verbose: 
			c, a = self.Value()
			if self.verbose: print(str(self.currentDate) + ' model: ' + self.modelName + ' _cash: ' + str(c) + ' Assets: ' + str(a))
		for ph in self.priceHistory:
			p = ph.GetPriceSnapshot(self.currentDate)
			self.ProcessDaysOrders(ph.stockTicker, p.open, p.high, p.low, p.close, self.currentDate)
		self.ReEvaluateTrancheCount()
		if withIncrement and self.currentDate <= self.modelEndDate: #increment the date
			try:
				loc = self.priceHistory[0].historicalPrices.index.get_loc(self.currentDate) + 1
				if loc < self.priceHistory[0].historicalPrices.shape[0]:
					nextDay = self.priceHistory[0].historicalPrices.index.values[loc]
					self.currentDate = ToDateTime(str(nextDay)[:10])
				else:
					print('The end: ' + str(self.modelEndDate))
					self.currentDate=self.modelEndDate		
			except:
				#print(self.priceHistory[0].historicalPrices)
				print('Unable to find next date in index from ', self.currentDate,  self.priceHistory[0].historicalPrices.stockTicker)
				self.currentDate += timedelta(days=1)
	
	def SetCustomValues(self, v1, v2):
		self.Custom1 = v1
		self.custom2 = v2
		
class ForcastModel():	#used to forecast the effect of a series of trade actions, one per day, and return the net change in value.  This will mirror the given model.  Can also be used to test alternate past actions 
	def __init__(self, mirroredModel:TradingModel, daysToForecast:int = 10):
		modelName = 'Forcaster for ' + mirroredModel.modelName
		self.daysToForecast = daysToForecast
		self.startDate = mirroredModel.modelStartDate 
		durationInYears = (mirroredModel.modelEndDate-mirroredModel.modelStartDate).days/365
		self.tm = TradingModel(modelName=modelName, startingTicker=mirroredModel._stockTickerList[0], startDate=mirroredModel.modelStartDate, durationInYears=durationInYears, totalFunds=mirroredModel.startingValue, verbose=False, trackHistory=False)
		self.savedModel = TradingModel(modelName=modelName, startingTicker=mirroredModel._stockTickerList[0], startDate=mirroredModel.modelStartDate, durationInYears=durationInYears, totalFunds=mirroredModel.startingValue, verbose=False, trackHistory=False)
		self.mirroredModel = mirroredModel
		self.tm._stockTickerList = mirroredModel._stockTickerList
		self.tm.priceHistory = mirroredModel.priceHistory
		self.savedModel._stockTickerList = mirroredModel._stockTickerList
		self.savedModel.priceHistory = mirroredModel.priceHistory

	def Reset(self, updateSavedModel:bool=True):
		if updateSavedModel:
			c, a = self.mirroredModel.Value()
			self.savedModel.currentDate = self.mirroredModel.currentDate
			self.savedModel._cash=self.mirroredModel._cash
			self.savedModel._fundsCommittedToOrders=self.mirroredModel._fundsCommittedToOrders
			self.savedModel.dailyValue = pd.DataFrame([[self.mirroredModel.currentDate,c,a,c+a]], columns=list(['Date','CashValue','AssetValue','TotalValue']))
			self.savedModel.dailyValue.set_index(['Date'], inplace=True)

			if len(self.savedModel._tranches) != len(self.mirroredModel._tranches):
				#print(len(self.savedModel._tranches), len(self.mirroredModel._tranches))
				tranchSize = self.mirroredModel._tranches[0].size
				tc = len(self.mirroredModel._tranches)
				while len(self.savedModel._tranches) < tc:
					self.savedModel._tranches.append(Tranche(tranchSize))
				while len(self.savedModel._tranches) > tc:
					self.savedModel._tranches.pop(-1)
				self.savedModel._tranchCount = len(self.savedModel._tranches)			
			for i in range(len(self.savedModel._tranches)):
				self.savedModel._tranches[i].ticker = self.mirroredModel._tranches[i].ticker
				self.savedModel._tranches[i].available = self.mirroredModel._tranches[i].available
				self.savedModel._tranches[i].size = self.mirroredModel._tranches[i].size
				self.savedModel._tranches[i].units = self.mirroredModel._tranches[i].units
				self.savedModel._tranches[i].purchased = self.mirroredModel._tranches[i].purchased
				self.savedModel._tranches[i].marketOrder = self.mirroredModel._tranches[i].marketOrder
				self.savedModel._tranches[i].sold = self.mirroredModel._tranches[i].sold
				self.savedModel._tranches[i].dateBuyOrderPlaced = self.mirroredModel._tranches[i].dateBuyOrderPlaced
				self.savedModel._tranches[i].dateBuyOrderFilled = self.mirroredModel._tranches[i].dateBuyOrderFilled
				self.savedModel._tranches[i].dateSellOrderPlaced = self.mirroredModel._tranches[i].dateSellOrderPlaced
				self.savedModel._tranches[i].dateSellOrderFilled = self.mirroredModel._tranches[i].dateSellOrderFilled
				self.savedModel._tranches[i].buyOrderPrice = self.mirroredModel._tranches[i].buyOrderPrice
				self.savedModel._tranches[i].purchasePrice = self.mirroredModel._tranches[i].purchasePrice
				self.savedModel._tranches[i].sellOrderPrice = self.mirroredModel._tranches[i].sellOrderPrice
				self.savedModel._tranches[i].sellPrice = self.mirroredModel._tranches[i].sellPrice
				self.savedModel._tranches[i].latestPrice = self.mirroredModel._tranches[i].latestPrice
				self.savedModel._tranches[i].expireAfterDays = self.mirroredModel._tranches[i].expireAfterDays
		c, a = self.savedModel.Value()
		self.startingValue = c + a
		self.tm.currentDate = self.savedModel.currentDate
		self.tm._cash=self.savedModel._cash
		self.tm._fundsCommittedToOrders=self.savedModel._fundsCommittedToOrders
		self.tm.dailyValue = pd.DataFrame([[self.savedModel.currentDate,c,a,c+a]], columns=list(['Date','CashValue','AssetValue','TotalValue']))
		self.tm.dailyValue.set_index(['Date'], inplace=True)
		if len(self.tm._tranches) != len(self.savedModel._tranches):
			#print(len(self.tm._tranches), len(self.savedModel._tranches))
			tranchSize = self.savedModel._tranches[0].size
			tc = len(self.savedModel._tranches)
			while len(self.tm._tranches) < tc:
				self.tm._tranches.append(Tranche(tranchSize))
			while len(self.tm._tranches) > tc:
				self.tm._tranches.pop(-1)
			self.tm._tranchCount = len(self.tm._tranches)			
		for i in range(len(self.tm._tranches)):
			self.tm._tranches[i].ticker = self.savedModel._tranches[i].ticker
			self.tm._tranches[i].available = self.savedModel._tranches[i].available
			self.tm._tranches[i].size = self.savedModel._tranches[i].size
			self.tm._tranches[i].units = self.savedModel._tranches[i].units
			self.tm._tranches[i].purchased = self.savedModel._tranches[i].purchased
			self.tm._tranches[i].marketOrder = self.savedModel._tranches[i].marketOrder
			self.tm._tranches[i].sold = self.savedModel._tranches[i].sold
			self.tm._tranches[i].dateBuyOrderPlaced = self.savedModel._tranches[i].dateBuyOrderPlaced
			self.tm._tranches[i].dateBuyOrderFilled = self.savedModel._tranches[i].dateBuyOrderFilled
			self.tm._tranches[i].dateSellOrderPlaced = self.savedModel._tranches[i].dateSellOrderPlaced
			self.tm._tranches[i].dateSellOrderFilled = self.savedModel._tranches[i].dateSellOrderFilled
			self.tm._tranches[i].buyOrderPrice = self.savedModel._tranches[i].buyOrderPrice
			self.tm._tranches[i].purchasePrice = self.savedModel._tranches[i].purchasePrice
			self.tm._tranches[i].sellOrderPrice = self.savedModel._tranches[i].sellOrderPrice
			self.tm._tranches[i].sellPrice = self.savedModel._tranches[i].sellPrice
			self.tm._tranches[i].latestPrice = self.savedModel._tranches[i].latestPrice
			self.tm._tranches[i].expireAfterDays = self.savedModel._tranches[i].expireAfterDays		
		c, a = self.tm.Value()
		if self.startingValue != c + a:
			print( 'Forcast model accounting error.  ', self.startingValue, self.mirroredModel.Value(), self.savedModel.Value(), self.tm.Value())
			assert(False)
			
	def GetResult(self):
		dayCounter = len(self.tm.dailyValue)
		while dayCounter <= self.daysToForecast:  
			self.tm.ProcessDay()
			dayCounter +=1
		c, a = self.tm.Value()
		endingValue = c + a
		return endingValue - self.startingValue
		
class StockPicker():
	def __init__(self, startDate:datetime=None, endDate:datetime=None): 
		self.priceData = []
		self._stockTickerList = []
		self._startDate = startDate
		self._endDate = endDate
		
	def __del__(self): 
		self.priceData = None
		self._stockTickerList = None
		
	def AddTicker(self, ticker:str):
		if not ticker in self._stockTickerList:
			p = PricingData(ticker)
			if p.LoadHistory(self._startDate, self._endDate, verbose=False): 
				p.CalculateStats()
				self.priceData.append(p)
				self._stockTickerList.append(ticker)

	def NormalizePrices(self):
		for i in range(len(self.priceData)):
			self.priceData[i].NormalizePrices()
			
	def FindOpportunities(self, currentDate:datetime, stocksToReturn:int = 5, filterOption:int = 3, minPercentGain=0.00): 
		result = []
		for i in range(len(self.priceData)):
			ticker = self.priceData[i].stockTicker
			psnap = self.priceData[i].GetPriceSnapshot(currentDate)
			if  ((psnap.shortEMA/psnap.longEMA)-1 > minPercentGain):
				if filterOption ==0: #Overbought
					if psnap.low > psnap.channelHigh: result.append(ticker)
				if filterOption ==1: #Oversold
					if psnap.high < psnap.channelLow: result.append(ticker)
				if filterOption ==1: #High price deviation
					if psnap.fiveDayDeviation > .0275: result.append(ticker)
		return result

	def GetHighestPriceMomentum(self, currentDate:datetime, longHistoryDays:int = 365, shortHistoryDays:int = 30, stocksToReturn:int = 5, filterOption:int = 3, minPercentGain=0.05, maxVolatility=.1, verbose:bool=False): 
		minDailyGain = minPercentGain/365
		candidates = pd.DataFrame(columns=list(['Ticker','hp2Year','hp1Year','hp6mo','hp3mo','hp2mo','hp1mo','currentPrice','2yearPriceChange','1yearPriceChange','6moPriceChange','3moPriceChange','2moPriceChange','1moPriceChange','dailyGain','monthlyGain','monthlyLossStd','longHistoricalValue','shortHistoricalValue','percentageChangeLongTerm','percentageChangeShortTerm','pointValue','Comments','latestEntry']))
		candidates.set_index(['Ticker'], inplace=True)
		lookBackDateLT = currentDate + timedelta(days=-longHistoryDays)
		lookBackDateST = currentDate + timedelta(days=-shortHistoryDays)
		for i in range(len(self.priceData)):
			ticker = self.priceData[i].stockTicker
			longHistoricalValue = self.priceData[i].GetPrice(lookBackDateLT)
			shortHistoricalValue = self.priceData[i].GetPrice(lookBackDateST)				
			s = self.priceData[i].GetPriceSnapshot(currentDate + timedelta(days=-730))
			hp2Year = s.fiveDayAverage
			s = self.priceData[i].GetPriceSnapshot(currentDate + timedelta(days=-365))
			hp1Year = s.fiveDayAverage
			s = self.priceData[i].GetPriceSnapshot(currentDate + timedelta(days=-180))
			hp6mo = s.fiveDayAverage
			s = self.priceData[i].GetPriceSnapshot(currentDate + timedelta(days=-90))
			hp3mo = s.fiveDayAverage
			s = self.priceData[i].GetPriceSnapshot(currentDate + timedelta(days=-60))
			hp2mo = s.fiveDayAverage
			s = self.priceData[i].GetPriceSnapshot(currentDate + timedelta(days=-30))
			hp1mo = s.fiveDayAverage
			s = self.priceData[i].GetPriceSnapshot(currentDate)
			#currentPrice = s.oneDayAverage	
			currentPrice = s.twoDayAverage	
			Comments = ''
			if s.low > s.channelHigh: 
				Comments += 'Overbought; '
			if s.high < s.channelLow: 
				Comments += 'Oversold; '
			if s.fiveDayDeviation > .0275: 
				Comments += 'HighDeviation; '
			percentageChangeShortTerm = 0
			percentageChangeLongTerm = 0
			if (longHistoricalValue > 0 and currentPrice > 0 and shortHistoricalValue > 0 and hp2Year > 0 and hp1Year > 0 and hp6mo > 0 and hp2mo > 0 and hp1mo > 0): #values were loaded
				percentageChangeLongTerm = ((currentPrice/longHistoricalValue)-1)/longHistoryDays
				percentageChangeShortTerm = ((currentPrice/shortHistoricalValue)-1)/shortHistoryDays
				pc1yr=((currentPrice/hp1Year)-1) 
				pc6mo=((currentPrice/hp6mo)-1) 
				pc3mo=((currentPrice/hp3mo)-1) 
				pc2mo=((currentPrice/hp2mo)-1) 
				pc1mo=((currentPrice/hp1mo)-1) 
				pointValue = round((10*pc1yr) + (10*pc6mo) + (10*pc3mo) + (10*pc1mo) - (3-10*s.monthlyLossStd))
				candidates.loc[ticker] = [hp2Year,hp1Year,hp6mo,hp3mo,hp2mo,hp1mo,currentPrice,(currentPrice/hp2Year)-1,(currentPrice/hp1Year)-1,(currentPrice/hp6mo)-1,(currentPrice/hp3mo)-1,(currentPrice/hp2mo)-1,(currentPrice/hp1mo)-1,s.dailyGain, s.monthlyGain, s.monthlyLossStd,longHistoricalValue,shortHistoricalValue,percentageChangeLongTerm, percentageChangeShortTerm, pointValue, Comments, self.priceData[i].historyEndDate]
			else:
				if currentPrice > 0 and verbose or True:
					if len(self.priceData[i].historicalPrices) > 0:
						print('Price load failed for ticker: ' + ticker, 'requested, history start, history end', currentDate, self.priceData[i].historyStartDate, self.priceData[i].historyEndDate, hp2Year,hp1Year,hp6mo,hp2mo,hp1mo)

		if filterOption ==1: #high performer, recently at a discount or slowing down but not negative
			filter = (candidates['percentageChangeLongTerm'] > candidates['percentageChangeShortTerm']) & (candidates['percentageChangeLongTerm'] > minDailyGain) & (candidates['percentageChangeShortTerm'] > 0) 
			candidates.sort_values('percentageChangeLongTerm', axis=0, ascending=False, inplace=True, kind='quicksort', na_position='last') #Most critical factor, sorting by largest long term gain
		elif filterOption ==2: #Long term gain meets min requirements
			filter = (candidates['percentageChangeLongTerm'] > minDailyGain) 
			candidates.sort_values('percentageChangeLongTerm', axis=0, ascending=False, inplace=True, kind='quicksort', na_position='last') #Most critical factor, sorting by largest long term gain
		elif filterOption ==3: #Best overall returns 25% average yearly over 36 years which choosing top 5 sorted by best yearly average
			filter = (candidates['percentageChangeLongTerm'] > minDailyGain) & (candidates['percentageChangeShortTerm'] > 0) 
			candidates.sort_values('percentageChangeLongTerm', axis=0, ascending=False, inplace=True, kind='quicksort', na_position='last') #Most critical factor, sorting by largest long term gain
		elif filterOption ==4: #Short term gain meets min requirements
			filter =  (candidates['percentageChangeShortTerm'] > minDailyGain) 
			candidates.sort_values('percentageChangeShortTerm', axis=0, ascending=False, inplace=True, kind='quicksort', na_position='last') #Most critical factor, sorting by largest short term gain, not effective
		elif filterOption ==44: #Short term gain meets min requirements, sort long value
			filter =  (candidates['percentageChangeShortTerm'] > minDailyGain) 
			candidates.sort_values('percentageChangeLongTerm', axis=0, ascending=False, inplace=True, kind='quicksort', na_position='last') #Most critical factor, sorting by largest long term gain
		elif filterOption ==5: #Point Value
			filter = (candidates['1yearPriceChange'] > minDailyGain) & (candidates['pointValue'] > 0)
			candidates.sort_values('pointValue', axis=0, ascending=False, inplace=True, kind='quicksort', na_position='last') 
		else: #no filter
			filter = (candidates['currentPrice'] > 0)
			candidates.sort_values('percentageChangeLongTerm', axis=0, ascending=False, inplace=True, kind='quicksort', na_position='last') #Most critical factor, sorting by largest long term gain
		candidates = candidates[filter]
		candidates.drop(columns=['longHistoricalValue','shortHistoricalValue','percentageChangeLongTerm','percentageChangeShortTerm'], inplace=True, axis=1)
		candidates = candidates[:stocksToReturn]
		return candidates

	def ToDataFrame(self, intervalInWeeks:int = 1, pivotOnTicker:bool = False, showGain:bool = True):
		r = pd.DataFrame()
		for i in range(len(self.priceData)):
			t = self.priceData[i].stockTicker
			if len(self.priceData[i].historicalPrices) > 0:
				x = self.priceData[i].historicalPrices.copy()
				if intervalInWeeks > 1:
					startDate = x.index[0]
					x['DayOffset'] = (x.index - startDate).days
					x = x[x['DayOffset'] % (intervalInWeeks * 7) ==0] #Drop all data except specified weekly interval of dates
					x.drop(columns=['DayOffset'], inplace=True, axis=1)
				if pivotOnTicker:
					if r.empty: r = pd.DataFrame(index=x.index)
					if showGain:
						r[t] = (x['Average']/x['Average'].shift(-1))
					else:
						r[t] = x['Average']				
				else:
					if showGain:
						x['Gain'] = x['Average']/x['Average'].shift(-1)
						x = x[['Gain']]
					x['Ticker'] = t
					if r.empty: 
						r = x
					else:
						r = r.append(x)
		r.fillna(value=0, inplace=True)
		r.sort_index
		return r
