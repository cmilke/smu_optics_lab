import visa
import time
import testing_utils



visa_resource_name = 'COM4'
register_value_file = 'register_values.dat'
fpga_confirmation_response = '33'
correct_status = [1,2,2,0,0]

fpga_uart_communication_protocol_template = [0x4E, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00]

strobe_command = [0x4E, 0x1B, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x1B, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00,
                  0x4E, 0x1B, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x1B, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

start_command = [0x4E, 0x1C, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x1C, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00,
                 0x4E, 0x1C, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x1C, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

read_command = [0x4F, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x20, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

param_check_array = [0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F, 0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x00, 0xFFF, 0x00]

correct_error_count = [0]*20
scan_time = 10 #seconds



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
    com10_instrument = visa.ResourceManager().open_resource(visa_resource_name,
                                                            open_timeout=10000, #10 seconds
                                                            resource_pyclass=pyvisa.resources.SerialInstrument,
                                                            baud_rate=115200,
                                                            data_bits=8,
                                                            parity=pyvisa.constants.Parity.none,
                                                            stop_bits = pyvisa.constants.StopBits.one)
    return com4_instrument



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
        command = bytes.fromhex( format(parameter,'02x') )
        visa.write_raw(command)
        response, status = fpga.visalib.read(fpga.session, 1 )
        if response != fpga_confirmation_response:
            print("WrongAck on parameter setting")
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
    fpga.write_raw(strobe_command_bytes)
    response, status = fpga.visalib.read(fpga.session, 2)
    if response != (fpga_confirmation_response + fpga_confirmation_response):
        print("WrongAck on start")
        exit(1)



def locx2_read(fpga):
    read_command_bytes = testing_utils.array_to_rawbytes(read_command) 
    fpga.write_raw(read_command_bytes)
    response, status = fpga.visalib.read(fpga.session, 208)
    return rawbytes_to_array(response)



def param_check(params):
    check_array  = params[1][0:2]
    check_array += params[1][8:12]
    check_array += params[1][25]
    check_array += params[1][24]
    check_array += params[1][26]
    check_array += [0xAA]
    return check_array



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
        error_count, params_read = data_extract(ack)

        error_count_is_wrong = error_count != correct_error_count
        params_read_are_wrong = params_read != params_written

        if error_count_is_wrong or params_read_are_wrong:
            reading_error = True
            break
        eleapsed_time = time.time() - scan_start_time


    #display where it failed in detail
    serial_close(fpga)


    
main()


