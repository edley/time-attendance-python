package smack.comm.sample.global;

import smack.comm.SBXPCProxy;
import smack.comm.output.OneStringOutput;

/**
 *
 * @author smackbio
 * @version 1.0
 */
public class SysUtil {
    public static long MachineNumber;
    public static final String NO_DEVICE = "No Device";
    public static final String WORKING = "Working...";
    public static final String TEMP_PHOTO_FILE = "C:\\TempPhoto.jpg";
    public static final long COMPRESSED_PHOTO_SIZE = 8192;
    
    public static String ErrorPrint(long errorCode)
    {
        switch((int)errorCode)
        {
            case 0:
                return "SUCCESS";
            case 1:
                return "ERR_COMPORT_ERROR";
            case 2:
                return "ERR_WRITE_FAIL";
            case 3:
                return "ERR_READ_FAIL";
            case 4:
                return "ERR_INVALID_PARAM";
            case 5:
                return "ERR_NON_CARRYOUT";
            case 6:
                return "ERR_LOG_END";
            case 7:
                return "ERR_MEMORY";
            case 8:
                return "ERR_MULTIUSER";
            default:
                return "";
        }
    }
    
    public static String pubLongToIPAddr(long value)
    {
        String ipAddr;
        long remain;
        remain = value % 256; if (remain < 0) remain = 256 + remain;
        ipAddr = String.valueOf(remain); value = (value - remain) / 256;
        remain = value % 256; if (remain < 0) remain = 256 + remain;
        ipAddr = String.valueOf(remain) +  "." + ipAddr; value = (value - remain) / 256;
        remain = value % 256; if (remain < 0) remain = 256 + remain;
        ipAddr = String.valueOf(remain) +  "." + ipAddr; value = (value - remain) / 256;
        remain = value % 256; if (remain < 0) remain = 256 + remain;
        ipAddr = String.valueOf(remain) + "." + ipAddr;
        return ipAddr;           
    }
    
    public static long pugIPAddrToLong(String ipAddr)
    {
        long dwIP;
        int k;
        String szTmp;
        k = ipAddr.indexOf('.');
        if(k == 0)
            return 0;
        try{ dwIP = Byte.parseByte(ipAddr.substring(0, k)); } catch (Exception e){ return 0; }
        ipAddr = ipAddr.substring(k + 1);
        
        k = ipAddr.indexOf('.');
        if(k == 0)
            return 0;
        try{ dwIP = dwIP*256 + Byte.parseByte(ipAddr.substring(0, k)); } catch (Exception e){ return 0; }
        ipAddr = ipAddr.substring(k + 1);
        
        k = ipAddr.indexOf('.');
        if(k == 0)
            return 0;
        try{ dwIP = dwIP*256 + Byte.parseByte(ipAddr.substring(0, k)); } catch (Exception e){ return 0; }
        ipAddr = ipAddr.substring(k);
        
        try{ dwIP = dwIP*256 + Byte.parseByte(ipAddr); } catch (Exception e){ return 0; }
        
        return dwIP;
    }
    
    public static OneStringOutput MakeXMLCommandHeader(String command)
    {
        OneStringOutput ret = new OneStringOutput();
        ret.value = "";
        ret = SBXPCProxy.XML_AddString(ret.value, "REQUEST", command);
        ret = SBXPCProxy.XML_AddString(ret.value, "MSGTYPE", "request");
        ret = SBXPCProxy.XML_AddInt(ret.value, "MachineID", (int)SysUtil.MachineNumber);
        return ret;
        
    }
    
    static
    {
        SysUtil.MachineNumber = 1;
    }
}
