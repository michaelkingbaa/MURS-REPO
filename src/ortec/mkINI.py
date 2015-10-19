import json

#This part is for setting gain's appropriately
hvSetting={'15226062':1100,
           '15226066':1100,
           '15194763':950,
       }
gain_stab_pars={'15226062':{'enable':True,'min':300,'mid':315,'max':330},
                '15226066':{'enable':True,'min':300,'mid':315,'max':330},
                '15194763':{'enable':True,'min':300,'mid':315,'max':330}}

fineGain={'15226062':0.6,
          '15226066':0.6,
          '15194763':0.6,
      }
data={'hv_setting':hvSetting,'gain_stab_pars':gain_stab_pars,'fine_gain':fineGain}
with open('ortec_config.ini','w') as f:
    json.dump(data,f)

