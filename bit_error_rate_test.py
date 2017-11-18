import LOCx2_SetReg
import main_LOCx2QA
import mx100tp_interface
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



def main_test(ref_clk_delay, sclk_delay, adc_name, test_time):
    LOCx2_SetReg.main(ref_clk_delay, sclk_delay, adc_name, usb_iss_resource_id)
    success_status = main_LOCx2QA.main(fpga_resource_id, test_time)
    return success_status



def find_optimal_delay_values(delay_success_list):
    print('find_opitmal_delay_values is undefined!')
    return 'lol'

    
    
for voltage, test_time in voltage_time_pair:
    mx100tp_interface.configure_voltage_level(mx100tp, 1, voltage)
    
    delay_success_list = []
    for ref_clk_delay in ref_clk_delay_list:
        sclk_delay_success_list = []
        for sclk_delay in sclk_delay_list:
            success = main_test(ref_clk_delay, sclk_delay, 'NevisADC', short_test_time)
            sclk_delay_success_list.append(success)
        delay_success_list.append(sclk_delay_success_list) 
    optimal_ref_clk_delay, optimal_sclk_delay = find_optimal_delay_values(delay_success_list)
    
    main_test(optimal_ref_clk_delay, optimal_sclk_delay, 'NevisADC', test_time)
    for adc_name in ['ADS5272', 'ADS5294', 'Testmode']:
        main_test(optimal_ref_clk_delay, optimal_sclk_delay, adc_name, tiny_test_time)   
mx100tp.close()