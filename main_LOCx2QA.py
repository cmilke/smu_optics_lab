import visa
import pyvisa
import time
import testing_utils



visa_resource_name = 'COM4'
register_value_file = 'register_values.dat'
fpga_confirmation_response = bytes('3','ascii')
correct_status = [1,2,2,0,0]

fpga_uart_communication_protocol_template = [0x4E, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00]

strobe_command = [0x4E, 0x1B, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x1B, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00,
                  0x4E, 0x1B, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x1B, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

start_command = [0x4E, 0x1C, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x1C, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00,
                 0x4E, 0x1C, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x1C, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

read_command = [0x4F, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

param_check_array = [0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F, 0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x00, 0xFFF, 0x00]

correct_error_count = [0]*20
scan_time = 10 #seconds


    
def stop(fpga,message):
    print(message)
    fpga.close()
    exit()
    
    

def read_register_values(file_name):
    register_values = []
    register_file = open(file_name)
    for line in register_file:
        register_string, value_string = line.split()
        register = int(register_string,16)
        value = int(value_string,16)
        register_values.append([register,value])
    return register_values



def open_serial_port(visa_resource_name):
    fpga = visa.ResourceManager().open_resource(visa_resource_name,
                                                            open_timeout=10000, #10 seconds
                                                            resource_pyclass=pyvisa.resources.SerialInstrument,
                                                            baud_rate=115200,
                                                            data_bits=8,
                                                            parity=pyvisa.constants.Parity.none,
                                                            stop_bits = pyvisa.constants.StopBits.one)
    return fpga



def paramameter_generator(register_values):
    parameter_list = []

    bit_slice = 256
    for pair in register_values:
        register = pair[0]
        value    = pair[1]
        value_remainder = value % bit_slice
        value_quotient = int(value / bit_slice)

        new_parameter = fpga_uart_communication_protocol_template[:]
        new_parameter[1] = register
        new_parameter[2] = value_remainder
        new_parameter[3] = value_quotient
        new_parameter[9] = register
        new_parameter[10] = value_remainder
        new_parameter[11] = value_quotient

        parameter_list.append(new_parameter)
    return parameter_list



def set_parameters(fpga, register_values):
    parameter_list = paramameter_generator(register_values)
    for parameter in parameter_list:
        command = testing_utils.array_to_rawbytes(parameter)
        print(parameter)
        fpga.write_raw(command)
        response, status = fpga.visalib.read(fpga.session, 1 )
        if response != fpga_confirmation_response:
            print("WrongAck on parameter setting")
            print("Given ACK value is: " + str(response))
            exit(1)
        time.sleep(0.1)



def param_strobe(fpga):
    strobe_command_bytes = testing_utils.array_to_rawbytes(strobe_command) 
    fpga.write_raw(strobe_command_bytes)
    response, status = fpga.visalib.read(fpga.session, 2)
    if response != (fpga_confirmation_response + fpga_confirmation_response):
        print("WrongAck on strobe")
        exit(1)



def locx2_start(fpga):
    start_command_bytes = testing_utils.array_to_rawbytes(start_command) 
    fpga.write_raw(start_command_bytes)
    response, status = fpga.visalib.read(fpga.session, 2)
    if response != (fpga_confirmation_response + fpga_confirmation_response):
        print("WrongAck on start")
        exit(1)



def locx2_read(fpga):
    read_command_bytes = testing_utils.array_to_rawbytes(read_command)
    fpga.write_raw(read_command_bytes)
    response, status = fpga.visalib.read(fpga.session, 208)
    return testing_utils.rawbytes_to_array(response)



def param_check(params):
    check_array  = [ params[0][1] ]
    check_array += [ params[1][1] ]
    check_array += [ params[8][1] ]
    check_array += [ params[9][1] ]
    check_array += [ params[10][1] ]
    check_array += [ params[11][1] ]
    check_array += [ params[25][1] ]
    check_array += [ params[24][1] ]
    check_array += [ params[26][1] ]
    check_array += [0xAA]
    print("check array equals: " + str(check_array))
    return check_array

    
#The values are loaded into the bitstring array BACKWARDS,
#and then flipped back around in the second-to-last step
#with the '[::-1]' construct.
def extract_check_value(ack_bits):
    split_locations = [ [0,8],[8,2],[10,2],[12,12] ]
    
    chunk_size = 5
    start_bit = 24
    num_chunks = 6
    split_locations += testing_utils.generate_consecutive_splits(start_bit, chunk_size, num_chunks)     
    check_list = testing_utils.assemble_bitstring_into_int_list(ack_bits, split_locations[::-1], True)
    return check_list
    


#As with the previous function, please note where the [::-1] is.
#The payload_error_count has to be loaded backwards
def extract_channel(ack_bits, sync_status_start, crc_flag_start, sync_loss_count_start, 
                    crc_error_count_start, payload_error_count_start):
    sync_status_size = 2
    crc_flag_size = 1
    error_count_length = 37
    num_payload_pieces = 8
    
    assembler_instructions = [ [sync_status_start,sync_status_size],
                               [crc_flag_start,crc_flag_size],
                               [sync_loss_count_start,sync_status_size],
                               [crc_error_count_start,error_count_length] ]
    
    assembler_instructions += testing_utils.generate_consecutive_splits(payload_error_count_start, error_count_length, num_payload_pieces)[::-1]
    channel_results = testing_utils.assemble_bitstring_into_int_list(ack_bits, assembler_instructions, True)
    return channel_results
    


def data_extract(ack):
    flipped_ack = []
    for n in range( 0, len(ack), 2):
        even_ack = ack[n]
        odd_ack = ack[n+1]
        flipped_ack.append(odd_ack)
        flipped_ack.append(even_ack)
    ack_bits = testing_utils.array_to_bitstring(flipped_ack,8,True)
    
    check_list = extract_check_value(ack_bits)
    print('\ncheck_list:')
    print(check_list)
    
    ch8_sync_status_start = 56
    ch8_crc_flag_start = 83
    ch8_sync_loss_count_start = 1021    
    ch8_crc_error_count_start = 281
    ch8_payload_error_count_start = 1354
    channel_8_results = extract_channel(ack_bits, ch8_sync_status_start, ch8_crc_flag_start, ch8_sync_loss_count_start, ch8_crc_error_count_start, ch8_payload_error_count_start)
    print('\nchannel 8 results:')
    testing_utils.print_hex_list(channel_8_results)
    
    ch9_sync_status_start = 54
    ch9_crc_flag_start = 82
    ch9_sync_loss_count_start = 984    
    ch9_crc_error_count_start = 281
    ch9_payload_error_count_start = 1058
    channel_9_results = extract_channel(ack_bits, ch9_sync_status_start, ch9_crc_flag_start, ch9_sync_loss_count_start, ch9_crc_error_count_start, ch9_payload_error_count_start)
    print('\nchannel 9 results:')
    print(channel_9_results)
    
    return(check_list, channel_8_results, channel_9_results)


def main():
    register_values = read_register_values(register_value_file)
    fpga = open_serial_port(visa_resource_name)
    set_parameters(fpga, register_values)
    param_strobe(fpga)
    locx2_start(fpga)
    time.sleep(0.1) #100 milliseconds
    locx2_read(fpga)
    params_written = param_check(register_values)

    reading_error = False
    elapsed_time = 0.0
    scan_start_time = time.time()
    while (elapsed_time < scan_time):
        ack = locx2_read(fpga)
        check_list, ch8_results, ch9_results = data_extract(ack)
        stop(fpga,'\nFinished without crash')

        error_count_is_wrong = error_count != correct_error_count
        params_read_are_wrong = params_read != params_written

        if error_count_is_wrong or params_read_are_wrong:
            reading_error = True
            break
        eleapsed_time = time.time() - scan_start_time


    #display where it failed in detail
    fpga.close()


	
main()


