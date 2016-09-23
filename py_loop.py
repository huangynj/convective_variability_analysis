import os
import sys

dates = ['2016052800', '2016052900', '2016053000', '2016053100', '2016060100', '2016060200',
         '2016060300', '2016060400', '2016060500', '2016060600', '2016060700', '2016060800']
# 0, 1, 2, 3, 4, 5
# 6, 7, 8, 9,10,11
dates = ['2016052800', '2016052900', '2016053000', '2016053100', '2016060100', '2016060200']
#dates = ['2016060300', '2016060400', '2016060500', '2016060600', '2016060700', '2016060800']
#dates = ['2016052800', '2016052900']
typ = sys.argv[1]
#dates = [sys.argv[2]]
for date in dates:
    if typ in ['compute', 'all']:
        print date
        #str1 = ('python compute_and_save.py --ana m --date ' + date + 
                    #' --nens 50 --tstart 3 --tend 24 --height 3000 ')
        #str2 = ('python compute_and_save.py --ana m --date ' + date + 
                    #' --nens 50 --tstart 3 --tend 24 --height 2000 ')
        #str3 = ('python compute_and_save.py --ana m --date ' + date + 
                    #' --nens 50 --tstart 3 --tend 24 --height 4000 ')
        #str4 = ('python compute_and_save.py --ana m --date ' + date + 
                    #' --nens 20 --tstart 3 --tend 24 --height 3000 ')
        #str5 = ('python compute_and_save.py --ana m --date ' + date + 
                    #' --nens 50 --tstart 3 --tend 24 --height 3000 --water False ')
        #os.system(str1 + ';' + str2 + ';' + str3 + ';'+ str4 + ';'+ str5 + '&')
        os.system('python compute_and_save.py --ana clouds --date ' + date + 
                    ' --nens 20 --tstart 3 --tend 24 --tinc 60 --height 3000 &')
    if typ in ['plot', 'all']:
        pass
        #os.system('python analyze_and_plot.py --ana m --date ' + date + 
                    #' --nens 20 --tstart 1 --tend 24 --height 2000 3000 5000 --plot all')
        
#python analyze_and_plot.py --ana m --date 2016052800 2016052900 2016053000 2016053100 2016060100 2016060200 2016060300 2016060400 2016060500 2016060600 2016060700 2016060800 --nens 20 --tstart 3 --tend 24 --height 500 1000 1500 2000 2500 3000 3500 4000 5000 6000 7000 8000 9000 10000 --plot height_var --tplot 6 9

#python analyze_and_plot.py --ana weather --date 2016052800 2016052900 2016053000 2016053100 2016060100 2016060200 2016060300 2016060400 2016060500 2016060600 2016060700 2016060800 --nens 20 --tstart 3 --tend 24 --height 3000 --plot summary_weather

#python analyze_and_plot.py --ana prec --date 2016052800 2016052900 2016053000 2016053100 2016060100 2016060200 2016060300 2016060400 2016060500 2016060600 2016060700 2016060800 --nens 20 --tstart 3 --tend 24 --height 3000 --plot prec_hist
