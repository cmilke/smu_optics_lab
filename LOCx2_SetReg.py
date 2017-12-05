import visa
import pyvisa
import time
import testing_utils



adc_enum = {'NevisADC':0, 'ADS5272':1, 'ADS5294':2, 'Testmode':3}
write_register_array = [0x0,0x2,0x4,0x6]
read_register_array = [0x1,0x3,0x5,0x7]
init_command = [0x5A,0x2,0x60]



#Be VERY CAREFUL with the ordering of bits in this function!
#The ordering flips directions multiple times.
def locx2_regs_gen(adc_type, ref_clk_delay, delay_array):
    delay_binary = []
    for i in range(4):
        delay_binary.append( testing_utils.to_bits(delay_array[i],8,True) )

    delay_piece0 = delay_binary[0][0:4]
    delay_piece1 = delay_binary[0][4]
    delay_piece2 = delay_binary[1][0:5]
    delay_piece3 = delay_binary[2][0:2]
    delay_piece4 = delay_binary[2][2:5]
    delay_piece5 = delay_binary[3][0:5]

    adc_type_binary = testing_utils.to_bits(adc_type,16,True)[0:2]
    ref_clk_delay_value_binary = testing_utils.to_bits(ref_clk_delay,8,True)[0:2]

    command_string1 = adc_type_binary + ref_clk_delay_value_binary + delay_piece0
    command_string2 = delay_piece1 + delay_piece2 + delay_piece3
    command_string3 = delay_piece4 + delay_piece5
    command1 = testing_utils.bitstring_to_integer(command_string1,True)
    command2 = testing_utils.bitstring_to_integer(command_string2,True)
    command3 = testing_utils.bitstring_to_integer(command_string3,True)

    generated_bytes = [13,command1,command2,command3]
    return generated_bytes



def open_usb_iss(visa_resource_name):
    usb_iss = visa.ResourceManager().open_resource(visa_resource_name)
    usb_iss.open_timeout=10000 #10 seconds
    usb_iss.baud_rate=9600
    usb_iss.data_bits=8
    usb_iss.resource_pyclass = pyvisa.resources.SerialInstrument
    usb_iss.parity = pyvisa.constants.Parity.none
    usb_iss.end_input = pyvisa.constants.SerialTermination.none
    usb_iss.read_termination = None
    usb_iss.write_termination = None
    usb_iss.stop_bits = pyvisa.constants.StopBits.one
    
    return usb_iss
    
    
    
def usb_12c_wr(visa_resource_name, write_mode, read_mode, command):
    usb_iss = open_usb_iss(visa_resource_name)
    if write_mode:
        command_bytes = testing_utils.array_to_rawbytes(command)
        usb_iss.write_raw(command_bytes)
    time.sleep(.5) #500 milliseconds
    data_read=-1
    if read_mode:
        bytes_to_read = usb_iss.bytes_in_buffer
        with usb_iss.ignore_warning(visa.constants.VI_SUCCESS_MAX_CNT):
            raw_byte, status = usb_iss.visalib.read(usb_iss.session, bytes_to_read )
        data_read = int.from_bytes(raw_byte, byteorder='big')
    usb_iss.close()
    return data_read



def main(ref_clk_delay, sclk_delay, adc_name, usb_iss_name, report):
    adc_type = adc_enum[adc_name]
    delay_array = [sclk_delay]*4
    generated_byte_array = locx2_regs_gen(adc_type, ref_clk_delay, delay_array)

    #Try setting parameter 10 times before giving up and failing
    read_comparison_failed = True
    max_number_of_setting_attempts = 10
    for attempt in range(max_number_of_setting_attempts):
        print("I2C attempt " + str(attempt) )
        print("I2C is filling registers")
        usb_12c_wr(usb_iss_name, True, False, init_command)
        for register_number in range( len(write_register_array) ):
            write_register = write_register_array[register_number]
            generated_byte = generated_byte_array[register_number]
            write_command = [0x53, write_register, generated_byte]
            usb_12c_wr(usb_iss_name, True, False, write_command)

        print("I2C is reading back registers")
        usb_12c_wr(usb_iss_name, True, False, init_command)
        for register_number in range( len(read_register_array) ):
            read_register = read_register_array[register_number]
            generated_byte = generated_byte_array[register_number]
            read_command = [0x53, read_register]
            data_read_out = usb_12c_wr(usb_iss_name, True, True, read_command)
            comparison_byte = data_read_out
            read_comparison_failed = comparison_byte != generated_byte
            if read_comparison_failed: break

        if not read_comparison_failed: break

    if read_comparison_failed:
        print("An error was encountered while reading back registers!")
    else:
        print("I2C has finished reading registers")
    return not read_comparison_failed
