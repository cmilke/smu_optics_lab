def print_hex_list(int_list):
    print('[',end='')
    for n in int_list[:-1]:
        print( format(n,'02x')+', ', end='' )
    print( format(int_list[-1],'02x')+']' )
        



def to_bits(value, number_of_bits, reverse):
    format_string = '0' + str(number_of_bits) + 'b'
    bit_string = format(value,format_string)
    if reverse:
        return bit_string[::-1]
    else:
        return bit_string



def bitstring_to_integer(bit_string, is_reversed):
    if is_reversed:
        return int(bit_string[::-1],2)
    else:
        return int(bit_string,2)


def array_to_bitstring(array, bits_per_element, reverse):
    bitstring = ''
    for value in array:
        bitstring += to_bits(value,bits_per_element,reverse)
    return bitstring
    
    
    
def rawbytes_to_array(rawbytes):
    array = []
    for value in rawbytes:
        array.append(value)
    return array
    
   
   
def array_to_rawbytes(array):
    rawbytes = bytes()
    for value in array:
        rawbytes += bytes.fromhex( format(value,'02x') )
    return rawbytes
    

    
#the 'assembler_instructions' argument is a list of (start,stop) tuples,
#which this function uses to break the bitstring up into pieces
def assemble_bitstring_into_int_list(bitstring, assembler_instructions, reversed):
    int_list = []
    for start,size in assembler_instructions:
        stop = start+size
        bit_chunk = bitstring[start:stop]
        int_value = bitstring_to_integer(bit_chunk,reversed)
        int_list.append(int_value)
    return int_list
    

    
def generate_consecutive_splits(start_bit, chunk_size, num_chunks):
    split_locations = []
    for chunk in range(num_chunks):
        split_start = start_bit+chunk*chunk_size
        split_locations.append([split_start,chunk_size])
    return split_locations

