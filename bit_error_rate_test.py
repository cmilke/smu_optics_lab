import LOCx2_SetReg
import main_LOCx2QA
import mx100tp_interface
import delay_time_selector
import visa
import time

usb_iss_resource_id = 'COM8'
fpga_resource_id = 'COM4'
mx100tp_resource_id = 'GPIB0::11::INSTR'

mx100tp = visa.ResourceManager().open_resource(mx100tp_resource_id)
voltage_time_pair = [(2.29,1.5),(2.8,1.5),(2.54,15)] #in (volts,minutes)
ref_clk_delay_list = [0,300,600] #pico-seconds
sclk_delay_list = range(12,25)
short_test_time = 5 #seconds
tiny_test_time = 2 #seconds
report = []



def main_test(ref_clk_delay, sclk_delay, adc_name, test_time, mx100tp, report):
    register_set_status = LOCx2_SetReg.main(ref_clk_delay, sclk_delay, adc_name, usb_iss_resource_id, report)
    if register_set_status != True:
        print('REGISTER SETTING FAILED! ABORTING!')
        mx100tp.close()
        exit(1)
    success_status = main_LOCx2QA.main(fpga_resource_id, test_time, mx100tp, report)
    return success_status



def find_optimal_delay_values(delay_success_list, report):
    optimal_delay_indices = delay_time_selector.select(delay_success_list)
    optimal_ref_clk_delay = ref_clk_delay_list[optimal_delay_indices[0]]
    optimal_sclk_delay = sclk_delay_list[optimal_delay_indices[1]]
    report.append( 'Optimal Ref_clk delay value chosen as: '+str(optimal_ref_clk_delay) )
    report.append( 'Optimal S_clk delay value chosen as: '+str(optimal_sclk_delay) )
    return (optimal_ref_clk_delay, optimal_sclk_delay)

    
    
test_chip_name = input('Enter Chip ID: ')
test_start_time = time.strftime('%m/%d/%Y     %H:%M:%S')
report_file_name = test_chip_name + '.txt'
header_line = 'Chip ID    '+test_chip_name+'    Test time    '+test_start_time
report.append(header_line)

for voltage, test_time in voltage_time_pair:
    #TODO: figure out which channel(s?) you are supposed to change
    mx100tp_interface.configure_voltage_level(mx100tp, 1, voltage)
    
    delay_success_list = []
    for ref_clk_delay in ref_clk_delay_list:
        sclk_delay_success_list = []
        for sclk_delay in sclk_delay_list:
            success = main_test(ref_clk_delay, sclk_delay, 'NevisADC', short_test_time, report)
            sclk_delay_success_list.append(success)
            print("FINISHED MAIN")
            mx100tp.close()
            exit(0)
        delay_success_list.append(sclk_delay_success_list)
    optimal_ref_clk_delay, optimal_sclk_delay = find_optimal_delay_values(delay_success_list)
    
    main_test(optimal_ref_clk_delay, optimal_sclk_delay, 'NevisADC', test_time)
    for adc_name in ['ADS5272', 'ADS5294', 'Testmode']:
        main_test(optimal_ref_clk_delay, optimal_sclk_delay, adc_name, mx100tp, tiny_test_time)   
mx100tp.close()

report_log = open(report_filename, 'w')
for line in report: report_log.write(line)
report_log.close()
