import zipfile
import struct

def parse_class_constant_pool(class_bytes):
    # ClassFile structure:
    # magic (4), minor (2), major (2), constant_pool_count (2)
    magic, minor, major, cp_count = struct.unpack('>IHHH', class_bytes[:10])
    if magic != 0xCAFEBABE:
        return []
    
    strings = []
    offset = 10
    i = 1
    while i < cp_count:
        tag = class_bytes[offset]
        offset += 1
        if tag == 1: # CONSTANT_Utf8
            length, = struct.unpack('>H', class_bytes[offset:offset+2])
            val = class_bytes[offset+2:offset+2+length].decode('utf-8', errors='ignore')
            strings.append(val)
            offset += 2 + length
            i += 1
        elif tag in (3, 4): # Integer, Float
            offset += 4
            i += 1
        elif tag in (5, 6): # Long, Double
            offset += 8
            i += 2 # takes 2 entries
        elif tag in (7, 8): # Class, String
            offset += 2
            i += 1
        elif tag in (9, 10, 11, 12): # Fieldref, Methodref, InterfaceMethodref, NameAndType
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
            # Unknown tag or others, just break or handle
            break
    return strings

if __name__ == '__main__':
    jar_path = '/Users/edley/Documents/ANT2/Java_SBXPCSample/SBXPCSample/lib/SBXPCSampleLIB.jar'
    with zipfile.ZipFile(jar_path) as z:
        for name in z.namelist():
            if name.endswith('.class'):
                class_bytes = z.read(name)
                strings = parse_class_constant_pool(class_bytes)
                # Check for JNI, native, Socket, loadLibrary
                native_methods = [s for s in strings if 'native' in s.lower() or 'socket' in s.lower() or 'library' in s.lower() or 'dll' in s.lower()]
                print(f"--- {name} ---")
                for s in sorted(list(set(strings))):
                    if any(x in s.lower() for x in ['socket', 'connect', 'port', 'ip', 'read', 'write', 'dll', 'loadlibrary', 'native']):
                        print("  ", s)
