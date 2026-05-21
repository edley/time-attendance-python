package smack.comm.sample;

import java.awt.EventQueue;
import java.awt.Font;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.text.DecimalFormat;
import java.text.NumberFormat;

import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JButton;
import javax.swing.JCheckBox;
import javax.swing.JComboBox;
import javax.swing.JTextField;
import javax.swing.SwingConstants;

import smack.comm.SBXPCProxy;
import smack.comm.input.DeviceInfoStatusInput;
import smack.comm.output.GetDeviceTimeOutput;
import smack.comm.output.OneLongOutput;
import smack.comm.sample.global.SysUtil;

import java.awt.event.ActionListener;
import java.awt.event.ActionEvent;

public class SystemInfoFrame extends JFrame {
	private JLabel lblMessage;
	private JButton btnGetDeviceTime;
	private JButton btnSetDeviceTime;
	private JButton btnPowerOnDevice;
	private JButton btnPowerOffDevice;
	private JButton btnEnableDevice;
	private JLabel lblStatusParameter;
	private JLabel lblInfoParameter;
	private JComboBox cmbParam;
	private JLabel lblStatusValue;
	private JTextField txtValue;
	private JButton btnGetDeviceInfo;
	private JButton btnSetDeviceInfo;
	private JButton btnGetDeviceStatus;
	private JCheckBox chkEnableDevice;

	/**
	 * Launch the application.
	 */
	public static void main(String[] args) {
		EventQueue.invokeLater(new Runnable() {
			public void run() {
				try {
					SystemInfoFrame frame = new SystemInfoFrame();
					frame.setVisible(true);
				} catch (Exception e) {
					e.printStackTrace();
				}
			}
		});
	}

	/**
	 * Create the frame.
	 */
	public SystemInfoFrame() {
		addWindowListener(new WindowAdapter() {
			@Override
			public void windowClosing(WindowEvent arg0) {
				if (MainFrame.getInstance() != null)
					MainFrame.getInstance().setVisible(true);
			}
		});
	
		setTitle("System Information");
		setBounds(100, 100, 469, 265);
		setDefaultCloseOperation(javax.swing.WindowConstants.DISPOSE_ON_CLOSE);
		getContentPane().setLayout(null);
		
		lblMessage = new JLabel("Message");
		lblMessage.setHorizontalAlignment(SwingConstants.CENTER);
		lblMessage.setFont(new Font("Segoe UI", Font.BOLD, 18));
		lblMessage.setBorder(javax.swing.BorderFactory.createBevelBorder(javax.swing.border.BevelBorder.LOWERED));
		lblMessage.setBounds(10, 11, 431, 35);
		getContentPane().add(lblMessage);
		
		btnGetDeviceTime = new JButton("GetDeviceTime");
		btnGetDeviceTime.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnGetDeviceTime_actionPerformed(arg0);
			}
		});
		btnGetDeviceTime.setBounds(10, 57, 137, 28);
		getContentPane().add(btnGetDeviceTime);
		
		btnSetDeviceTime = new JButton("SetDeviceTime");
		btnSetDeviceTime.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnSetDeviceTime_actionPerformed(arg0);
			}
		});
		btnSetDeviceTime.setBounds(10, 91, 137, 28);
		getContentPane().add(btnSetDeviceTime);
		
		btnPowerOnDevice = new JButton("PowerOnDevice");
		btnPowerOnDevice.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnPowerOnDevice_actionPerformed(arg0);
			}
		});
		btnPowerOnDevice.setBounds(157, 57, 137, 28);
		getContentPane().add(btnPowerOnDevice);
		
		btnPowerOffDevice = new JButton("PowerOffDevice");
		btnPowerOffDevice.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnPowerOffDevice_actionPerformed(arg0);
			}
		});
		btnPowerOffDevice.setBounds(157, 91, 137, 28);
		getContentPane().add(btnPowerOffDevice);
		
		btnEnableDevice = new JButton("DisableDevice");
		btnEnableDevice.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnEnableDevice_actionPerformed(arg0);
			}
		});
		btnEnableDevice.setBounds(304, 57, 137, 28);
		getContentPane().add(btnEnableDevice);
		
		lblStatusParameter = new JLabel("Status Parameter:");
		lblStatusParameter.setBounds(10, 139, 126, 14);
		getContentPane().add(lblStatusParameter);
		
		lblInfoParameter = new JLabel("Info Parameter:");
		lblInfoParameter.setBounds(10, 160, 126, 14);
		getContentPane().add(lblInfoParameter);
		
		cmbParam = new JComboBox();
		cmbParam.setModel(new javax.swing.DefaultComboBoxModel(new String[] { "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", " " }));
		cmbParam.setBounds(143, 139, 83, 28);
		getContentPane().add(cmbParam);
		
		lblStatusValue = new JLabel("Status Value:");
		lblStatusValue.setBounds(254, 139, 83, 23);
		getContentPane().add(lblStatusValue);
		
		txtValue = new JTextField();
		txtValue.setBounds(344, 139, 97, 28);
		getContentPane().add(txtValue);
		txtValue.setColumns(10);
		
		btnGetDeviceInfo = new JButton("GetDeviceInfo");
		btnGetDeviceInfo.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnGetDeviceInfo_actionPerformed(arg0);
			}
		});
		btnGetDeviceInfo.setBounds(10, 185, 137, 28);
		getContentPane().add(btnGetDeviceInfo);
		
		btnSetDeviceInfo = new JButton("SetDeviceInfo");
		btnSetDeviceInfo.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnSetDeviceInfo_actionPerformed(arg0);
			}
		});
		btnSetDeviceInfo.setBounds(157, 185, 137, 28);
		getContentPane().add(btnSetDeviceInfo);
		
		btnGetDeviceStatus = new JButton("GetDeviceStatus");
		btnGetDeviceStatus.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnGetDeviceStatus_actionPerformed(arg0);
			}
		});
		btnGetDeviceStatus.setBounds(304, 185, 137, 28);
		getContentPane().add(btnGetDeviceStatus);
		
		chkEnableDevice = new JCheckBox("");
		chkEnableDevice.setBounds(356, 91, 21, 23);
		getContentPane().add(chkEnableDevice);

	}
	
    private void btnGetDeviceTime_actionPerformed(ActionEvent evt) {
        boolean ret;
        int errorCode;
        
        lblMessage.setText(SysUtil.WORKING);
        invalidate();
        
        ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, false);
        
        if(!ret)
        {
            lblMessage.setText(SysUtil.NO_DEVICE);
            return;
        }
        
        GetDeviceTimeOutput output;
        output = SBXPCProxy.GetDeviceTime(SysUtil.MachineNumber);
        
        NumberFormat formatter = new DecimalFormat("00");
        if(output.isSuccess())
        {
            String timeString = output.dwYear + "/" + formatter.format(output.dwMonth) + "/" + formatter.format(output.dwDay) + " ";
            timeString += formatter.format(output.dwHour) + ":" + formatter.format(output.dwMinute) + ":" + formatter.format(output.dwSecond);
            lblMessage.setText(timeString);
            errorCode = 0;
        }else
        {
            errorCode = (int)SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;
            lblMessage.setText(SysUtil.ErrorPrint(errorCode));
        }
        
        ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
    }

    private void btnSetDeviceTime_actionPerformed(ActionEvent evt) {
        boolean ret;
        int errorCode;
        
        lblMessage.setText(SysUtil.WORKING);
        invalidate();
        
        ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, false);
        
        if(!ret)
        {
            lblMessage.setText(SysUtil.NO_DEVICE);
            return;
        }
        
        ret  = SBXPCProxy.SetDeviceTime(SysUtil.MachineNumber);
        
        if(ret)
            errorCode = 0;
        else
            errorCode = (int)SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;
        
        lblMessage.setText(SysUtil.ErrorPrint(errorCode));
        
        ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
    }

    private void btnPowerOnDevice_actionPerformed(ActionEvent evt) {
        SBXPCProxy.PowerOnAllDevice(SysUtil.MachineNumber);
    }

    private void btnPowerOffDevice_actionPerformed(ActionEvent evt) {
        boolean ret;
        int errorCode;
        
        lblMessage.setText(SysUtil.WORKING);
        invalidate();
        
        ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, false);
        
        if(!ret)
        {
            lblMessage.setText(SysUtil.NO_DEVICE);
            return;
        }
        
        ret  = SBXPCProxy.PowerOffDevice(SysUtil.MachineNumber);
        
        if(ret)
            errorCode = 0;
        else
            errorCode = (int)SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;
        
        lblMessage.setText(SysUtil.ErrorPrint(errorCode));
        
        ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
    }

    private void btnEnableDevice_actionPerformed(ActionEvent evt) {
        boolean ret;
        
        lblMessage.setText(SysUtil.WORKING);
        invalidate();
        
        if(chkEnableDevice.isSelected())
        {
            ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
            
            if(!ret)
            {
                lblMessage.setText(SysUtil.NO_DEVICE);
                return;
            }
            
            lblMessage.setText("Enable Device Success");
            btnEnableDevice.setText("Disable Device");
            chkEnableDevice.setSelected(false);
        }else
        {
            ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, false);
            
            if(!ret)
            {
                lblMessage.setText(SysUtil.NO_DEVICE);
                return;
            }
            
            lblMessage.setText("Disable Device Success");
            btnEnableDevice.setText("Enable Device");
            chkEnableDevice.setSelected(true);
        }
    }

    private void btnGetDeviceInfo_actionPerformed(ActionEvent evt) {
        boolean ret;
        int errorCode;
        
        lblMessage.setText(SysUtil.WORKING);
        invalidate();
        
        ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, false);
        
        if(!ret)
        {
            lblMessage.setText(SysUtil.NO_DEVICE);
            return;
        }
        
        DeviceInfoStatusInput input = new DeviceInfoStatusInput();
        input.dwMachineNumber = SysUtil.MachineNumber;
        input.dwInfoStatusIndex = cmbParam.getSelectedIndex() + 1;
        
        OneLongOutput output;
        output = SBXPCProxy.GetDeviceInfo(input);
        
        if(output.isSuccess())
        {
            errorCode = 0;
            String message = "";
            switch((int)input.dwInfoStatusIndex)
            {
                case 1:  message = "(1) = ManagerCount = " + output.dwValue; break;
                case 2:  message = "(2) = Device ID = " + output.dwValue; break;
                case 3:  message = "(3) = Language = " + output.dwValue; break;
                case 4:  message = "(4) = PowerOffTime = " + output.dwValue; break;
                case 5:  message = "(5) = Lock release time = " + output.dwValue; break;
                case 6:  message = "(6) = GLogWarning = " + output.dwValue; break;
                case 7:  message = "(7) = SLogWarning = " + output.dwValue; break;
                case 8:  message = "(8) = ReVerifyTime = " + output.dwValue; break;
                case 9:  message = "(9) = Baudrate = " + output.dwValue; break;
                case 10: message = "(10) = Parity check = " + output.dwValue; break;
                case 11: message = "(11) = Stop bit = " + output.dwValue; break;
                case 12: message = "(12) = Date Seperator = " + output.dwValue; break;
                case 13: message = "(13) = Identificatin mode = " + output.dwValue; break;
                case 14: message = "(14) = LockOperate = " + output.dwValue; break;
                case 15: message = "(15) = Door sensor type = " + output.dwValue; break;
                case 16: message = "(16) = Door open time limit = " + output.dwValue; break;
                case 17: message = "(17) = Anti-pass = " + output.dwValue; break;
                case 18: message = "(18) = Auto sleep time = " + output.dwValue; break;
                case 19: message = "(19) = Daylight offset = " + output.dwValue; break;
                case 20: message = "(20) = UDP Server = " + SysUtil.pubLongToIPAddr(output.dwValue);
                case 21: message = "(21) = DHCP Use = " + output.dwValue; break;
                case 22: message = "(22) = NOT SUPPORTED = ";
                case 23: message = "(23) = Manager PC IP Address = " + SysUtil.pubLongToIPAddr(output.dwValue);
                case 24: message = "(24) = Event Send Type = " + output.dwValue; break;
            }
            lblMessage.setText(message);
        }
        else
        {
            errorCode = (int)SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;
            lblMessage.setText(SysUtil.ErrorPrint(errorCode));
        }
        
        ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
    }

    private void btnSetDeviceInfo_actionPerformed(ActionEvent evt) {
        boolean ret;
        int errorCode;
        DeviceInfoStatusInput input = new DeviceInfoStatusInput();
        input.dwMachineNumber = SysUtil.MachineNumber;
        input.dwInfoStatusIndex = cmbParam.getSelectedIndex() + 1;
        
        long dwValue;
        
        try{
            dwValue = Long.parseLong(txtValue.getText());
        }catch(Exception e)
        {
            lblMessage.setText("Invalid Format!");
            return;
        }
        
        if(input.dwInfoStatusIndex == 20 || input.dwInfoStatusIndex == 23)
            dwValue = SysUtil.pugIPAddrToLong(txtValue.getText());
        
        lblMessage.setText(SysUtil.WORKING);
        invalidate();
        
        ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, false);
        
        if(!ret)
        {
            lblMessage.setText(SysUtil.NO_DEVICE);
            return;
        }
        
        
        ret = SBXPCProxy.SetDeviceInfo(input, dwValue);
        
        if(ret)
            errorCode = 0;
        else
            errorCode = (int)SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;
        
        lblMessage.setText(SysUtil.ErrorPrint(errorCode));
        
        ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
    }

    private void btnGetDeviceStatus_actionPerformed(ActionEvent evt) {
        boolean ret;
        int errorCode;
        
        lblMessage.setText(SysUtil.WORKING);
        invalidate();
        
        ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, false);
        
        if(!ret)
        {
            lblMessage.setText(SysUtil.NO_DEVICE);
            return;
        }
        
        DeviceInfoStatusInput input = new DeviceInfoStatusInput();
        input.dwMachineNumber = SysUtil.MachineNumber;
        input.dwInfoStatusIndex = cmbParam.getSelectedIndex() + 1;
        
        OneLongOutput output;
        output = SBXPCProxy.GetDeviceStatus(input);
        
        if(output.isSuccess())
        {
            errorCode = 0;
            String message = "";
            switch((int)input.dwInfoStatusIndex)
            {
                case 1:  message = "(1) = Manager count = " + output.dwValue; break;
                case 2:  message = "(2) = User count = " + output.dwValue; break;
                case 3:  message = "(3) = Fp count = " + output.dwValue; break;
                case 4:  message = "(4) = Password count = " + output.dwValue; break;
                case 5:  message = "(5) = SLog count = " + output.dwValue; break;
                case 6:  message = "(6) = GLog count = " + output.dwValue; break;
                case 7:  message = "(7) = Card count = " + output.dwValue; break;
                case 8:  message = "(8) = Alarm status = " + output.dwValue; break;
            }
            lblMessage.setText(message);
        }
        else
        {
            errorCode = (int)SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;
            lblMessage.setText(SysUtil.ErrorPrint(errorCode));
        }
        
        ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
    }
}
