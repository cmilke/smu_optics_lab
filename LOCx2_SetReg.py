import visa
import time



com10_visa_string = 'COM10'
error_status = (False, 0, '')
adc_type = 0x0001 #FIXME: this is an enum with 4 options
ref_clk_delay = 0 #FIXME: I think this is also an enum...
delay_array = [0x17,0x17,0x17,0x17]
write_register_array = [0x0,0x2,0x4,0x6]
read_register_array = [0x1,0x3,0x5,0x7]
init_command = [0x5A,0x02,0x60]


def to_bits(value, number_of_bits, reverse):
    format_string = '0' + str(number_of_bits) + 'b'
    bit_string = format(value,format_string)[::-1]
    if reverse:
        return bit_string[::-1]
    else:
        return bit_string

def to_integer(bit_string, is_reversed):
    if is_reversed:
        return int(bit_string[::-1],2)
    else:
        return int(bit_string,2)



#Be VERY CAREFUL with the ordering of bits in this function!
#The ordering flips directions multiple times.
def locx2_regs_gen(adc_type, ref_clk_delay, delay_array):
    delay_binary = []
    for i in range(4): delay_binary.append( to_bits(delay_array[i],8,True) )

    delay_piece0 = delay_binary[0][0:4]
    delay_piece1 = delay_binary[0][4]
    delay_piece2 = delay_binary[1][0:5]
    delay_piece3 = delay_binary[2][0:2]
    delay_piece4 = delay_binary[2][2:5]
    delay_piece5 = delay_binary[3][0:5]

    adc_type_binary = to_bits(adc_type,16,True)[0:2]
    ref_clk_delay_value = [0x0,0x1,0x3][ref_clk_delay]
    ref_clk_delay_value_binary = to_bits(ref_clk_delay_value,8,True)[0:2]

    command_string1 = adc_type_binary + ref_clk_delay_value_binary + delay_piece0
    command_string2 = delay_piece1 + delay_piece2 + delay_piece3
    command_string3 = delay_piece4 + delay_piece5

    command1 = to_integer(command_string1,True)
    command2 = to_integer(command_string2,True)
    command3 = to_integer(command_string3,True)

    generated_bytes = [13,command1,command2,command3]
    return generated_bytes



def usb_12c_wr(visa_resource_name, write_mode, read_mode, command, error_status):
    com10_instrument = visa.ResourceManager().open_resource(visa_resource_name,
                                                            open_timeout=10000, #10 seconds
                                                            resource_pyclass=pyvisa.resources.SerialInstrument,
                                                            baud_rate=9600,
                                                            data_bits=8,
                                                            parity=pyvisa.constants.Parity.none,
                                                            stop_bits = pyvisa.constants.StopBits.one)

    if write_mode:
        com10_instrument.write( chr(write_string) )
    time.sleep(0.5) #500 milliseconds
    data_read=-1
    if read_mode:
        data_read = com10_instrument.read()

    #TODO: display read string and bytes read
    return (error_status, data_read)



#TODO: make this more elaborate
def display_test_results(test_passed):
    print('Did test pass? ' + str(test_passed) )



generated_byte_array = locx2_regs_gen(adc_type, ref_clk_delay, delay_array)

error_status = usb_12c_wr(com10_visa_string, True, False, init_command, error_status)[0]
for register_number in range( size(write_register_array) ):
    write_register = write_register_array[register_number]
    generated_byte = generated_byte_array[register_number]
    write_command = [0x53, write_register, generated_byte]
    error_status = usb_12c_wr(com10_visa_string, True, False, write_command, error_status)[0]
    #TODO: print write_command out


error_status = usb_12c_wr(com10_visa_string, True, False, init_command, error_status)[0]
values_read = []
read_comparison_failed = False
for register_number in range( size(read_register_array) ):
    read_register = read_register_array[register_number]
    generated_byte = generated_byte_array[register_number]
    read_command = [0x53, read_register]
    error_status, data_read_out = usb_12c_wr(com10_visa_string, True, True, read_command, error_status)
    #TODO: print read_command out

    comparison_byte = data_read_out[0]
    values_read.append(comparison_byte)
    read_comparison_failed = comparison_byte != generated_byte
    if read_comparison_failed: break

#if (error_status[0] or read_comparison_failed):
if read_comparison_failed
    display_test_results(False)

#print generated_byte_array
