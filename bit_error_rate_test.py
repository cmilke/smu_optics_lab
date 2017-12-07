import LOCx2_SetReg
import main_LOCx2QA
import mx100tp_interface
import delay_time_selector
import visa
import time

#usb_iss_resource_id = 'COM8'
#fpga_resource_id = 'COM4'
usb_iss_resource_id = 'ASRL7::INSTR'
fpga_resource_id = 'ASRL8::INSTR'
mx100tp_resource_id = 'GPIB0::11::INSTR'

mx100tp = visa.ResourceManager().open_resource(mx100tp_resource_id)
voltage_time_pair = [(2.29,1.5),(2.8,1.5),(2.54,15)] #in (volts,minutes)
ref_clk_delay_list = [0,300,600] #pico-seconds
sclk_delay_list = range(12,25)
adc_type = ['NevisADC', 'ADS5272', 'ADS5294', 'Testmode']
short_test_time = 5 #seconds
tiny_test_time = 2 #seconds
report_filename = ''
report = []



def log_output(report):
    report_log = open(report_filename, 'a')
    for line in report:
        report_log.write(line+'\n')
    report_log.close()
    del report[:]



def main_test(ref_clk_delay, sclk_delay, adc_name, test_time, mx100tp, report):
    register_set_status = LOCx2_SetReg.main(ref_clk_delay, sclk_delay, adc_name, usb_iss_resource_id, report)
    if register_set_status != True:
        err_message = 'REGISTER SETTING FAILED! ABORTING!'
        print(err_message)
        report.append(err_message)
        log_output(report)
        mx100tp.close()
        exit(1)
    report.append('ASIC ADC type = 0   FPGA ADC type = ' + adc_name)
    success_status = main_LOCx2QA.main(fpga_resource_id, test_time, mx100tp, report)
    success = int( not success_status )

    log_output(report)
    return success



def find_optimal_delay_values(delay_success_list, report):
    optimal_delay_indices = delay_time_selector.select(delay_success_list, report)
    optimal_ref_clk_delay = ref_clk_delay_list[optimal_delay_indices[0]]
    optimal_sclk_delay = sclk_delay_list[optimal_delay_indices[1]]
    report.append( 'Optimal Ref_clk delay value chosen as: '+str(optimal_ref_clk_delay) )
    report.append( 'Optimal S_clk delay value chosen as: '+str(optimal_sclk_delay) )
    return (optimal_ref_clk_delay, optimal_sclk_delay)

    
    
test_chip_name = input('Enter Chip ID: ')
test_start_time = time.strftime('%m/%d/%Y     %H:%M:%S')
report_filename = test_chip_name + '.txt'
report_log = open(report_filename, 'w')
report_log.close()
header_line = 'Chip ID    '+test_chip_name+'    Test time    '+test_start_time
report.append(header_line)

all_voltages_successful = True
for voltage, test_time_minutes in voltage_time_pair:
    success_list = []
    mx100tp_interface.configure_voltage_level(mx100tp, 1, voltage)
    report.append('\n\nVDD (V) = ' + str(voltage))
    
    print('\n####################################')
    print('     Voltage Set to ' + str(voltage) + '     ')
    print('### Beginning Delay Optimisation ###')
    print('####################################\n')
    delay_success_list = []
    for ref_clk_delay in ref_clk_delay_list:
        sclk_delay_success_list = []
        for sclk_delay in sclk_delay_list:
            print('\n###Testing (refclk,sclk) delay: '+str(ref_clk_delay)+','+str(sclk_delay)+'###\n')
            success = main_test(ref_clk_delay, sclk_delay, adc_type[0], short_test_time, mx100tp, report)
            sclk_delay_success_list.append(success)
        delay_success_list.append(sclk_delay_success_list)
    optimal_ref_clk_delay, optimal_sclk_delay = find_optimal_delay_values(delay_success_list, report)
    report.append('\nBeggining long-term testing')
    log_output(report)

    print('\n##############################') 
    print('### Beginning Primary Test ###')
    print('##############################\n') 
    test_time = test_time_minutes*60 #minutes to seconds
    main_success = main_test(optimal_ref_clk_delay, optimal_sclk_delay, adc_type[0], test_time, mx100tp, report)
    success_list.append(main_success)
    report.append('Primary test success = ' + str(main_success))
    log_output(report)

    print('\n#############################') 
    print('### Beginning ADC Testing ###')
    print('#############################\n') 
    for adc_name in adc_type[1:]:
        adc_success = main_test(optimal_ref_clk_delay, optimal_sclk_delay, adc_name, tiny_test_time, mx100tp, report)   
        success_list.append(not adc_success)
        report.append('ADC ' + adc_name + ' success = ' + str(adc_success))
        log_output(report)

    full_success = ( success_list == [True]*4 )
    success_string = 'Testing for voltage level ' + str(voltage)
    if full_success: success_string += ' was a full success!'
    else:
        success_string += ' encountered errors!'
        all_voltages_successful = False
    report.append(success_string)
    log_output(report)
mx100tp.close()


print('\n###########################') 
print('### ALL TESTS COMPLETED ###')
print('###########################\n') 
if all_voltages_successful:
    report.append('\nAll tests were completed succesfully!')
else:
    report.append('\nSome tests encountered errors')
log_output(report)
