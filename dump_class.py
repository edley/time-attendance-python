import zipfile
import struct

def parse_fields_and_methods(class_bytes):
    # ClassFile structure:
    # magic (4), minor (2), major (2), constant_pool_count (2)
    magic, minor, major, cp_count = struct.unpack('>IHHH', class_bytes[:10])
    if magic != 0xCAFEBABE:
        return []
    
    # Read Constant Pool
    cp = [None] * cp_count
    offset = 10
    i = 1
    while i < cp_count:
        tag = class_bytes[offset]
        offset += 1
        if tag == 1: # CONSTANT_Utf8
            length, = struct.unpack('>H', class_bytes[offset:offset+2])
            val = class_bytes[offset+2:offset+2+length].decode('utf-8', errors='ignore')
            cp[i] = ('Utf8', val)
            offset += 2 + length
            i += 1
        elif tag == 3: # Integer
            val, = struct.unpack('>i', class_bytes[offset:offset+4])
            cp[i] = ('Integer', val)
            offset += 4
            i += 1
        elif tag == 4: # Float
            val, = struct.unpack('>f', class_bytes[offset:offset+4])
            cp[i] = ('Float', val)
            offset += 4
            i += 1
        elif tag == 5: # Long
            val, = struct.unpack('>q', class_bytes[offset:offset+8])
            cp[i] = ('Long', val)
            offset += 8
            i += 2
        elif tag == 6: # Double
            val, = struct.unpack('>d', class_bytes[offset:offset+8])
            cp[i] = ('Double', val)
            offset += 8
            i += 2
        elif tag in (7, 8): # Class (7), String (8)
            val, = struct.unpack('>H', class_bytes[offset:offset+2])
            cp[i] = (tag, val)
            offset += 2
            i += 1
        elif tag in (9, 10, 11, 12): # Fieldref, Methodref, InterfaceMethodref, NameAndType
            v1, v2 = struct.unpack('>HH', class_bytes[offset:offset+4])
            cp[i] = (tag, v1, v2)
            offset += 4
            i += 1
        elif tag == 15: # MethodHandle
            offset += 3
            i += 1
        elif tag == 16: # MethodType
            offset += 2
            i += 1
        elif tag == 18: # InvokeDynamic
            offset += 4
            i += 1
        else:
            break
            
    # access_flags (2), this_class (2), super_class (2), interfaces_count (2)
    access_flags, this_class, super_class, interfaces_count = struct.unpack('>HHHH', class_bytes[offset:offset+8])
    offset += 8 + 2 * interfaces_count
    
    # fields_count (2)
    fields_count, = struct.unpack('>H', class_bytes[offset:offset+2])
    offset += 2
    
    fields = []
    for _ in range(fields_count):
        acc, name_idx, desc_idx, attr_count = struct.unpack('>HHHH', class_bytes[offset:offset+8])
        offset += 8
        for _ in range(attr_count):
            attr_name_idx, attr_len = struct.unpack('>HI', class_bytes[offset:offset+6])
            offset += 6 + attr_len
        fields.append((cp[name_idx][1], cp[desc_idx][1]))
        
    # methods_count (2)
    methods_count, = struct.unpack('>H', class_bytes[offset:offset+2])
    offset += 2
    
    methods = []
    for _ in range(methods_count):
        acc, name_idx, desc_idx, attr_count = struct.unpack('>HHHH', class_bytes[offset:offset+8])
        offset += 8
        for _ in range(attr_count):
            attr_name_idx, attr_len = struct.unpack('>HI', class_bytes[offset:offset+6])
            offset += 6 + attr_len
        methods.append((cp[name_idx][1], cp[desc_idx][1]))
        
    return fields, methods

if __name__ == '__main__':
    jar_path = '/Users/edley/Documents/ANT2/Java_SBXPCSample/SBXPCSample/lib/SBXPCSampleLIB.jar'
    with zipfile.ZipFile(jar_path) as z:
        for name in ['smack/comm/data/GeneralLogData.class', 'smack/comm/data/SuperLogData.class', 'smack/comm/SBXPCProxy.class']:
            class_bytes = z.read(name)
            fields, methods = parse_fields_and_methods(class_bytes)
            print(f"\n================ {name} ================")
            print("Fields:")
            for f in fields:
                print(f"  {f[0]}: {f[1]}")
            print("Methods:")
            for m in methods:
                print(f"  {m[0]}: {m[1]}")
