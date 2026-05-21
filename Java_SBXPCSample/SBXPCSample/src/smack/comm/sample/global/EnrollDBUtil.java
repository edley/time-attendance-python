package smack.comm.sample.global;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.sql.Connection;
import java.sql.Driver;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.List;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 *
 * @author smackbio
 * @version 1.0
 */
public class EnrollDBUtil {
    public static final String SQL_COLUMN_MACHINE_NO = "EMachineNumber";
    public static final String SQL_COLUMN_ENROLL_NO = "EnrollNumber";
    public static final String SQL_COLUMN_FINGER_NO = "FingerNumber";
    public static final String SQL_COLUMN_PRIVILEGE = "Privilige";
    public static final String SQL_COLUMN_PASSWORD = "Password";
    public static final String SQL_COLUMN_FPDATA = "FPData";
    
    public static final String SQL_ENROLL_NEW = "INSERT INTO tblEnroll("
                                                + SQL_COLUMN_MACHINE_NO + ", "
                                                + SQL_COLUMN_ENROLL_NO + ", "
                                                + SQL_COLUMN_FINGER_NO + ", "
                                                + SQL_COLUMN_PRIVILEGE + ", "
                                                + SQL_COLUMN_PASSWORD + ", "
                                                + SQL_COLUMN_FPDATA + ") VALUES(?, ?, ?, ?, ?, ?)";
    
    public static final String SQL_ENROLL_UPDATE = "UPDATE tblEnroll SET "
                                                + SQL_COLUMN_PRIVILEGE + " = ?, "
                                                + SQL_COLUMN_PASSWORD + " = ?, "
                                                + SQL_COLUMN_FPDATA + " = ? "
                                                + "WHERE "
                                                + SQL_COLUMN_MACHINE_NO + " = ? AND "
                                                + SQL_COLUMN_ENROLL_NO + " = ? AND "
                                                + SQL_COLUMN_FINGER_NO + " = ?";

    public static final String SQL_ENROLL_SELECT = "SELECT * FROM tblEnroll WHERE "
                                                + SQL_COLUMN_MACHINE_NO + " = ? AND "
                                                + SQL_COLUMN_ENROLL_NO + " = ? AND "
                                                + SQL_COLUMN_FINGER_NO + " = ?";
    
    public static final String SQL_ENROLL_SELECT_ALL = "SELECT "
                                                + SQL_COLUMN_MACHINE_NO + ", "
                                                + SQL_COLUMN_ENROLL_NO + ", "
                                                + SQL_COLUMN_FINGER_NO + ", "
                                                + SQL_COLUMN_PRIVILEGE + ", "
                                                + SQL_COLUMN_PASSWORD + ", "
                                                + SQL_COLUMN_FPDATA + " FROM tblEnroll "
                                                + "WHERE " + SQL_COLUMN_MACHINE_NO + " = ?";            

    public static final String SQL_ENROLL_DELETE_ALL = "DELETE * FROM tblEnroll WHERE " + SQL_COLUMN_MACHINE_NO + " = ?";
    
    public static boolean newEnrollData(UserEnrollData enrollData) throws SQLException
    {
        Connection conn = EnrollDBDataSource.getConnection();
        if(conn == null)
            return false;
        
        PreparedStatement stm = null;
        try{
            stm = conn.prepareStatement(SQL_ENROLL_NEW);
            stm.setInt(1, enrollData.machineNo);
            stm.setInt(2, enrollData.enrollNo);
            stm.setInt(3, enrollData.fingerNo);
            stm.setInt(4, enrollData.privilege);
            stm.setInt(5, enrollData.password);
            byte[] fpDataBuf = new byte[enrollData.fpData.length * 5];
            int iValue;
            for(int i = 0; i < enrollData.fpData.length; i ++)
            {
                iValue = Math.abs(enrollData.fpData[i]);
                fpDataBuf[i * 5 + 4] = (byte)(iValue % 256); iValue /= 256;
                fpDataBuf[i * 5 + 3] = (byte)(iValue % 256); iValue /= 256;
                fpDataBuf[i * 5 + 2] = (byte)(iValue % 256); iValue /= 256;
                fpDataBuf[i * 5 + 1] = (byte)(iValue % 256);
                fpDataBuf[i * 5 + 0] = (byte)(enrollData.fpData[i] > 0 ? 0 : 1);
            }
            ByteArrayInputStream bis = new ByteArrayInputStream(fpDataBuf);
            stm.setBinaryStream(6, bis, bis.available());
            
            int ret = stm.executeUpdate();
            return ret == 1;
        }finally
        {
            conn.commit();
            if(stm != null)
                stm.close();
            conn.close();
        }
    }
    
    public static boolean updateEnrollData(UserEnrollData enrollData) throws SQLException
    {
        if(!EnrollDBUtil.isExistEnrollData(enrollData))
            return newEnrollData(enrollData);
            
        Connection conn = EnrollDBDataSource.getConnection();
        if(conn == null)
            return false;
        
        PreparedStatement stm = null;
        try{
            stm = conn.prepareStatement(SQL_ENROLL_UPDATE);
            stm.setInt(1, enrollData.privilege);
            stm.setInt(2, enrollData.password);
            byte[] fpDataBuf = new byte[enrollData.fpData.length * 5];
            int iValue;
            for(int i = 0; i < enrollData.fpData.length; i ++)
            {
                iValue = Math.abs(enrollData.fpData[i]);
                fpDataBuf[i * 5 + 4] = (byte)(iValue % 256); iValue /= 256;
                fpDataBuf[i * 5 + 3] = (byte)(iValue % 256); iValue /= 256;
                fpDataBuf[i * 5 + 2] = (byte)(iValue % 256); iValue /= 256;
                fpDataBuf[i * 5 + 1] = (byte)(iValue % 256);
                fpDataBuf[i * 5 + 0] = (byte)(enrollData.fpData[i] < 0 ? 1 : 0);
            }
            ByteArrayInputStream bis = new ByteArrayInputStream(fpDataBuf);
            stm.setBinaryStream(3, bis, bis.available());

            stm.setInt(4, enrollData.machineNo);
            stm.setInt(5, enrollData.enrollNo);
            stm.setInt(6, enrollData.fingerNo);
            
            int ret = stm.executeUpdate();
            return ret == 1;
        }finally
        {
            conn.commit();
            if(stm != null)
                stm.close();
            conn.close();
        }
    }
    
    public static int getAllEnrollData(long machineNo, List<UserEnrollData> enrollDataList) throws SQLException
    {
        Connection conn = EnrollDBDataSource.getConnection();
        if(conn == null)
            return 0;
        
        PreparedStatement stm = null;
        ResultSet rst = null;
        UserEnrollData enrollData;
        try{
            stm = conn.prepareStatement(SQL_ENROLL_SELECT_ALL);
            stm.setInt(1, (int)machineNo);

            rst = stm.executeQuery();
            
            int len; int temp;
            while(rst.next())
            {
                enrollData = new UserEnrollData();
                enrollData.machineNo = rst.getInt(SQL_COLUMN_MACHINE_NO);
                enrollData.enrollNo = rst.getInt(SQL_COLUMN_ENROLL_NO);
                enrollData.fingerNo = rst.getInt(SQL_COLUMN_FINGER_NO);
                enrollData.password = rst.getInt(SQL_COLUMN_PASSWORD);
                enrollData.privilege = rst.getInt(SQL_COLUMN_PRIVILEGE);
                byte[] fpDataBuf = rst.getBytes(SQL_COLUMN_FPDATA);
                
                len = fpDataBuf.length / 5;
                enrollData.fpData = new int[len];
                for(int i = 0; i < len; i ++)
                {
                    enrollData.fpData[i] = 0;
                    for(int j = 1; j < 5; j ++)
                    {
                        temp = fpDataBuf[i * 5 + j];
                        temp = (temp < 0 ? temp + 256 : temp);
                        enrollData.fpData[i] = enrollData.fpData[i] * 256 + temp;
                    }
                    if(fpDataBuf[i * 5] > 0)
                        enrollData.fpData[i] = -enrollData.fpData[i];
                }
                enrollDataList.add(enrollData);
            }
            
            return enrollDataList.size();
        }finally
        {
            conn.commit();
            if(rst != null) rst.close();
            if(stm != null) stm.close();
            conn.close();
        }
    }
    
    public static boolean deleteAllEnrollData(long machineNo) throws SQLException
    {
        Connection conn = EnrollDBDataSource.getConnection();
        if(conn == null)
            return false;
        
        PreparedStatement stm = null;
        try{
            stm = conn.prepareStatement(SQL_ENROLL_DELETE_ALL);
            stm.setInt(1, (int)machineNo);
            
            int ret = stm.executeUpdate();

            return ret > 0;
        }finally
        {
            conn.commit();
            if(stm != null)
                stm.close();
            conn.close();
        }
    }
    
    public static boolean isExistEnrollData(UserEnrollData enrollData) throws SQLException
    {
        Connection conn = EnrollDBDataSource.getConnection();
        if(conn == null)
            return true;
        
        PreparedStatement stm = null;
        ResultSet rst = null;
        try{
            stm = conn.prepareStatement(SQL_ENROLL_SELECT);
            stm.setInt(1, enrollData.machineNo);
            stm.setInt(2, enrollData.enrollNo);
            stm.setInt(3, enrollData.fingerNo);

            rst = stm.executeQuery();
            
            return rst.next();
        }finally
        {
            conn.commit();
            if(rst != null) rst.close();
            if(stm != null) stm.close();
            conn.close();
        }
    }
    
    public boolean deleteAllEnrollData() throws SQLException
    {
        Connection conn = EnrollDBDataSource.getConnection();
        if(conn == null)
            return true;
        
        PreparedStatement stm = null;
        try{
            stm = conn.prepareStatement(SQL_ENROLL_DELETE_ALL);

            int ret = stm.executeUpdate();
            
            return true;
        }finally
        {
            conn.commit();
            if(stm != null) stm.close();
            conn.close();
        }
    }
}

class EnrollDBDataSource
{
    public static Connection getConnection()
    {
//        try {
//            Driver d = (Driver)Class.forName("sun.jdbc.odbc.JdbcOdbcDriver").newInstance();
//            return DriverManager.getConnection("jdbc:odbc:Driver={Microsoft Access Driver (*.mdb)};DBQ=db/datEnrollDat.mdb");
//        } catch (SQLException ex) {
//            Logger.getLogger(EnrollDBDataSource.class.getName()).log(Level.SEVERE, null, ex);
//        } catch (ClassNotFoundException ex) {
//            Logger.getLogger(EnrollDBDataSource.class.getName()).log(Level.SEVERE, null, ex);
//        } catch (InstantiationException ex) {
//            Logger.getLogger(EnrollDBDataSource.class.getName()).log(Level.SEVERE, null, ex);
//        } catch (IllegalAccessException ex) {
//            Logger.getLogger(EnrollDBDataSource.class.getName()).log(Level.SEVERE, null, ex);
//        }
    	
		try {
			return DriverManager.getConnection(
			        "jdbc:ucanaccess://./db/datEnrollDat.accdb");
		} catch (SQLException ex) {
			Logger.getLogger(EnrollDBDataSource.class.getName()).log(Level.SEVERE, null, ex);
		} 
        return null;
    }
}