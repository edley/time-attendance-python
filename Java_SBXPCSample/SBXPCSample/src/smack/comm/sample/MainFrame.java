package smack.comm.sample;

import java.awt.Color;
import java.awt.EventQueue;
import java.awt.Font;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;

import javax.swing.ButtonGroup;
import javax.swing.DefaultComboBoxModel;
import javax.swing.JButton;
import javax.swing.JComboBox;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JRadioButton;
import javax.swing.JTextField;
import javax.swing.SwingConstants;
import javax.swing.UIManager;
import javax.swing.border.TitledBorder;
import javax.swing.event.ChangeEvent;
import javax.swing.event.ChangeListener;

import smack.comm.SBXPCProxy;
import smack.comm.output.ConnectP2POutput;
import smack.comm.sample.global.SysUtil;

public class MainFrame extends JFrame {

   
	enum ConnectMode
    {
    	Network,
    	viaP2P,
    }
	
	private static MainFrame frame = null;
	
	public static MainFrame getInstance() {
		return frame;
	}
	
	 /**
	 * Launch the application.
	 */
	public static void main(String[] args) {
		EventQueue.invokeLater(new Runnable() {
			public void run() {
				try {
					frame = new MainFrame();
					frame.setVisible(true);
				} catch (Exception e) {
					e.printStackTrace();
				}
			}
		});
	}
	    
    private JButton btnAccessTz;
    private JButton btnBellTime;
    private JButton btnClose;
    private JButton btnDepartment;
    private JButton btnEnroll;
    private JButton btnLockControl;
    private JButton btnLog;
    private JButton btnOpen;
    private JButton btnProductCode;
    private JButton btnProxy;
    private JButton btnSysInfo;
    private JButton btnTrMode;
    private JComboBox cmbBaudrate;
    private JComboBox cmbCommPort;
    private JComboBox cmbMachineNumber;
    private JRadioButton optNetwork;
    private JRadioButton optSerial;
    private JRadioButton optUsb;
    private JRadioButton optViaP2P;
    private ButtonGroup radiobuttongroup;
    private JTextField txtDeviceUID;
    private JTextField txtIPAddress; 
	private JTextField txtPassword;
    private JTextField txtPortNumber;
    
    /**
	 * Create the frame.
	 */
	public MainFrame() {
		
    	addWindowListener(new WindowAdapter() {
    		@Override
    		public void windowClosed(WindowEvent arg0) {
    	        SBXPCProxy.Disconnect(SysUtil.MachineNumber);
    	    }
    	});
    	
		setTitle("SBXPC Sample");
		setBounds(100, 100, 494, 540);
		setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
		getContentPane().setLayout(null);
		
		JLabel lblSbxpcSample = new JLabel("SBXPC Sample");
		lblSbxpcSample.setFont(new Font("Tahoma", Font.PLAIN, 32));
		lblSbxpcSample.setForeground(Color.RED);
		lblSbxpcSample.setBounds(10, 11, 458, 39);
		getContentPane().add(lblSbxpcSample);
		lblSbxpcSample.setHorizontalAlignment(SwingConstants.CENTER);
		
		JLabel lblProduct = new JLabel("M50");
		lblProduct.setForeground(Color.BLUE);
		lblProduct.setFont(new Font("Tahoma", Font.ITALIC, 18));
		lblProduct.setBounds(10, 51, 458, 24);
		getContentPane().add(lblProduct);
		lblProduct.setHorizontalAlignment(SwingConstants.CENTER);
		
		JPanel panelConnect = new JPanel();
		panelConnect.setBounds(10, 75, 458, 53);
		getContentPane().add(panelConnect);
		panelConnect.setToolTipText("");
		panelConnect.setBorder(new TitledBorder(null, "Connect", TitledBorder.LEADING, TitledBorder.TOP, null, null));
		
		JLabel lblMachineNumber = new JLabel("Machine Number :");
		lblMachineNumber.setHorizontalAlignment(SwingConstants.RIGHT);
		lblMachineNumber.setBounds(10, 22, 114, 14);
		
		cmbMachineNumber = new JComboBox();
		cmbMachineNumber.setBounds(134, 19, 72, 20);
		cmbMachineNumber.setModel(new DefaultComboBoxModel(new String[] {"1", "2", "3", "4", "5", "6", "7", "8"}));
		
		btnOpen = new JButton("Open");
		btnOpen.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnOpenActionPerformed(arg0);
			}
		});
		btnOpen.setBounds(283, 13, 72, 30);
		
		btnClose = new JButton("Close");
		btnClose.setEnabled(false);
		btnClose.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnCloseActionPerformed(arg0);
			}
		});
		btnClose.setBounds(365, 13, 72, 30);
		panelConnect.setLayout(null);
		panelConnect.add(lblMachineNumber);
		panelConnect.add(cmbMachineNumber);
		panelConnect.add(btnOpen);
		panelConnect.add(btnClose);
		
		optNetwork = new JRadioButton("Network");
		optNetwork.setSelected(true);
		optNetwork.addChangeListener(new ChangeListener() {
			public void stateChanged(ChangeEvent arg0) {
				optNetworkStateChanged(arg0);
			}
		});
		
		optViaP2P = new JRadioButton("P2P");
		optNetwork.setBounds(215, 139, 81, 15);
		getContentPane().add(optNetwork);
		this.optViaP2P.addChangeListener(new ChangeListener() {
			public void stateChanged(ChangeEvent arg0) {
				optViaP2PStateChanged(arg0);
			}
		});
		this.optViaP2P.setBounds(340, 139, 54, 15);
		
		getContentPane().add(this.optViaP2P);
		
		JPanel panelNetwork = new JPanel();
		panelNetwork.setBounds(207, 146, 261, 137);
		getContentPane().add(panelNetwork);
		panelNetwork.setToolTipText("");
		panelNetwork.setBorder(new TitledBorder(null, "", TitledBorder.LEADING, TitledBorder.TOP, null, null));
		
		JLabel lblIpAddress = new JLabel("IP Address :");
		lblIpAddress.setHorizontalAlignment(SwingConstants.RIGHT);
		lblIpAddress.setBounds(10, 24, 92, 14);
		
		txtIPAddress = new JTextField();
		txtIPAddress.setText("192.168.1.224");
		txtIPAddress.setBounds(112, 21, 128, 20);
		txtIPAddress.setColumns(10);
		panelNetwork.setLayout(null);
		panelNetwork.add(lblIpAddress);
		panelNetwork.add(txtIPAddress);
		
		JLabel lblPortNumber = new JLabel("Port Number :");
		lblPortNumber.setHorizontalAlignment(SwingConstants.RIGHT);
		lblPortNumber.setBounds(10, 52, 92, 14);
		panelNetwork.add(lblPortNumber);
		
		txtPortNumber = new JTextField();
		txtPortNumber.setText("5005");
		txtPortNumber.setColumns(10);
		txtPortNumber.setBounds(112, 49, 128, 20);
		panelNetwork.add(txtPortNumber);
		
		JLabel lblPassword = new JLabel("Password :");
		lblPassword.setHorizontalAlignment(SwingConstants.RIGHT);
		lblPassword.setBounds(10, 80, 92, 14);
		panelNetwork.add(lblPassword);
		
		txtPassword = new JTextField();
		txtPassword.setText("0");
		txtPassword.setColumns(10);
		txtPassword.setBounds(112, 77, 128, 20);
		panelNetwork.add(txtPassword);
		
		JLabel lblDeviceUid = new JLabel("Device UID :");
		lblDeviceUid.setHorizontalAlignment(SwingConstants.RIGHT);
		lblDeviceUid.setBounds(10, 108, 92, 14);
		panelNetwork.add(lblDeviceUid);
		
		txtDeviceUID = new JTextField();
		txtDeviceUID.setEnabled(false);
		txtDeviceUID.setColumns(10);
		txtDeviceUID.setBounds(112, 105, 128, 20);
		panelNetwork.add(txtDeviceUID);
		
		optSerial = new JRadioButton("Serial Device");
		this.optSerial.setEnabled(false);
		optSerial.addChangeListener(new ChangeListener() {
			public void stateChanged(ChangeEvent arg0) {
				optSerialStateChanged(arg0);
			}
		});
		optSerial.setBounds(18, 139, 102, 15);
		getContentPane().add(optSerial);
		
		JPanel panelSerial = new JPanel();
		panelSerial.setLayout(null);
		panelSerial.setToolTipText("");
		panelSerial.setBorder(new TitledBorder(null, "", TitledBorder.LEADING, TitledBorder.TOP, null, null));
		panelSerial.setBounds(10, 146, 187, 86);
		getContentPane().add(panelSerial);
		
		JLabel lblComport = new JLabel("ComPort :");
		lblComport.setEnabled(false);
		lblComport.setHorizontalAlignment(SwingConstants.RIGHT);
		lblComport.setBounds(10, 24, 71, 14);
		panelSerial.add(lblComport);
		
		JLabel lblBaudrate = new JLabel("Baudrate :");
		lblBaudrate.setEnabled(false);
		lblBaudrate.setHorizontalAlignment(SwingConstants.RIGHT);
		lblBaudrate.setBounds(10, 52, 71, 14);
		panelSerial.add(lblBaudrate);
		
		cmbCommPort = new JComboBox();
		this.cmbCommPort.setEnabled(false);
		cmbCommPort.setModel(new DefaultComboBoxModel(new String[] {"COM1", "COM2", "COM3", "COM4", "COM5", "COM6"}));
		cmbCommPort.setBounds(91, 21, 72, 20);
		panelSerial.add(cmbCommPort);
		
		cmbBaudrate = new JComboBox();
		this.cmbBaudrate.setEnabled(false);
		cmbBaudrate.setModel(new DefaultComboBoxModel(new String[] {"9600", "19200", "38400", "57600", "115200"}));
		this.cmbBaudrate.setSelectedIndex(4);
		cmbBaudrate.setBounds(91, 49, 72, 20);
		panelSerial.add(cmbBaudrate);
		
		optUsb = new JRadioButton("USB Device");
		this.optUsb.setEnabled(false);
		optUsb.addChangeListener(new ChangeListener() {
			public void stateChanged(ChangeEvent arg0) {
				optSerialStateChanged(arg0);
			}
		});
		optUsb.setBounds(18, 251, 123, 15);
		getContentPane().add(optUsb);
		
		JPanel panelManagement = new JPanel();
		panelManagement.setLayout(null);
		panelManagement.setToolTipText("");
		panelManagement.setBorder(new TitledBorder(UIManager.getBorder("TitledBorder.border"), "Management", TitledBorder.LEADING, TitledBorder.TOP, null, new Color(0, 0, 0)));
		panelManagement.setBounds(10, 294, 459, 195);
		getContentPane().add(panelManagement);
		
		btnEnroll = new JButton("Enroll Data Management");
		this.btnEnroll.setEnabled(false);
		btnEnroll.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnEnrollActionPerformed(arg0);
			}
		});
		btnEnroll.setBounds(15, 26, 184, 30);
		panelManagement.add(btnEnroll);
		
		btnLog = new JButton("Log Data Management");
		this.btnLog.setEnabled(false);
		btnLog.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnLogActionPerformed(arg0);
			}
		});
		btnLog.setBounds(15, 68, 184, 30);
		panelManagement.add(btnLog);
		
		btnSysInfo = new JButton("System Info");
		this.btnSysInfo.setEnabled(false);
		btnSysInfo.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnSysInfoActionPerformed(arg0);
			}
		});
		btnSysInfo.setBounds(214, 26, 106, 30);
		panelManagement.add(btnSysInfo);
		
		btnLockControl = new JButton("Lock Control");
		this.btnLockControl.setEnabled(false);
		btnLockControl.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnLockControlActionPerformed(arg0);
			}
		});
		btnLockControl.setBounds(330, 26, 106, 30);
		panelManagement.add(btnLockControl);
		
		btnBellTime = new JButton("Bell Time");
		this.btnBellTime.setEnabled(false);
		btnBellTime.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnBellTimeActionPerformed(arg0);
			}
		});
		btnBellTime.setBounds(214, 68, 106, 30);
		panelManagement.add(btnBellTime);
		
		btnTrMode = new JButton("Log TZone");
		this.btnTrMode.setEnabled(false);
		btnTrMode.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnTrModeActionPerformed(arg0);
			}
		});
		btnTrMode.setBounds(330, 68, 106, 30);
		panelManagement.add(btnTrMode);
		
		btnProductCode = new JButton("Get SN");
		this.btnProductCode.setEnabled(false);
		btnProductCode.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnProductCodeActionPerformed(arg0);
			}
		});
		btnProductCode.setBounds(214, 110, 106, 30);
		panelManagement.add(btnProductCode);
		
		btnAccessTz = new JButton("Access TZone");
		this.btnAccessTz.setEnabled(false);
		btnAccessTz.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnAccessTzActionPerformed(arg0);
			}
		});
		btnAccessTz.setBounds(330, 110, 106, 30);
		panelManagement.add(btnAccessTz);
		
		btnDepartment = new JButton("Department");
		this.btnDepartment.setEnabled(false);
		btnDepartment.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnDepartmentActionPerformed(arg0);
			}
		});
		btnDepartment.setBounds(214, 152, 106, 30);
		panelManagement.add(btnDepartment);
		
		btnProxy = new JButton("DaiGong");
		this.btnProxy.setEnabled(false);
		btnProxy.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnDepartmentActionPerformed(arg0);
			}
		});
		btnProxy.setBounds(330, 152, 106, 30);
		panelManagement.add(btnProxy);
		
		radiobuttongroup = new ButtonGroup();
		radiobuttongroup.add(optUsb);
		radiobuttongroup.add(optSerial);
		radiobuttongroup.add(optNetwork);
		radiobuttongroup.add(optViaP2P);
	}
	
    private void btnAccessTzActionPerformed(java.awt.event.ActionEvent evt) {//GEN-FIRST:event_btnAccessTzActionPerformed
        AccessTzFrame accessTz_frame = new AccessTzFrame();
        accessTz_frame.setVisible(true);
        setVisible(false);
    }

    private void btnBellTimeActionPerformed(java.awt.event.ActionEvent evt) {//GEN-FIRST:event_btnBellTimeActionPerformed
        BellSettingFrame bellSetting_frame = new BellSettingFrame();
        bellSetting_frame.setVisible(true);
        setVisible(false);
    }
	
	private void btnCloseActionPerformed(java.awt.event.ActionEvent evt) {//GEN-FIRST:event_btnCloseActionPerformed
        SBXPCProxy.Disconnect(SysUtil.MachineNumber);
        enableManagementGroup(false);
    }
	
    private void btnDepartmentActionPerformed(java.awt.event.ActionEvent evt) {//GEN-FIRST:event_btnDepartmentActionPerformed
        DepartmentFrame department_frame = new DepartmentFrame();
        department_frame.setVisible(true);
        setVisible(false);
    }

    private void btnEnrollActionPerformed(java.awt.event.ActionEvent evt) {
        EnrollMngFrame enroll_frame = new EnrollMngFrame();
        enroll_frame.setVisible(true);
        setVisible(false);
    }

    private void btnLockControlActionPerformed(java.awt.event.ActionEvent evt) {//GEN-FIRST:event_btnLockControlActionPerformed
        LockControlFrame lockControl_frame = new LockControlFrame();
        lockControl_frame.setVisible(true);
        setVisible(false);
    }

    private void btnLogActionPerformed(java.awt.event.ActionEvent evt) {
        LogMngFrame logMngFrame = new LogMngFrame();
        logMngFrame.setVisible(true);
        setVisible(false);
    }

    private void btnOpenActionPerformed(java.awt.event.ActionEvent evt) {//GEN-FIRST:event_btnOpenActionPerformed
        boolean ret = false;
        if(optNetwork.isSelected())
        {
            ret = SBXPCProxy.ConnectTcpip(  SysUtil.MachineNumber, 
                                            txtIPAddress.getText(), 
                                            Long.parseLong(txtPortNumber.getText()), 
                                            Long.parseLong(txtPassword.getText())
                                         );
        }
        else if (optViaP2P.isSelected())
        {
        	if (txtDeviceUID.getText().length() >= 6 && txtDeviceUID.getText().length() <= 16)
			{
	        	ConnectP2POutput output = SBXPCProxy.ConnectP2P(
	        			txtDeviceUID.getText(),
	        			txtIPAddress.getText(), 
	                    Long.parseLong(txtPortNumber.getText()), 
	                    Long.parseLong(txtPassword.getText())
	                 );
	        	ret = handleP2PResult(output);
			}
        	else
        	{
        		txtDeviceUID.grabFocus();
        		JOptionPane.showMessageDialog(null, "Please input Device UID correctly!", "Invalid DeviceUID.", JOptionPane.INFORMATION_MESSAGE);
        	}
        }
        else
        {
            long baudrate = Long.parseLong(cmbBaudrate.getSelectedItem().toString());
            ret = SBXPCProxy.ConnectSerial(SysUtil.MachineNumber, cmbCommPort.getSelectedIndex(), baudrate);
        }
        enableManagementGroup(ret);
    }

    private void btnProductCodeActionPerformed(java.awt.event.ActionEvent evt) {//GEN-FIRST:event_btnProductCodeActionPerformed
        ProductCodeFrame productCode_frame = new ProductCodeFrame();
        productCode_frame.setVisible(true);
        setVisible(false);
    }

    private void btnProxyActionPerformed(java.awt.event.ActionEvent evt) {//GEN-FIRST:event_btnProxyActionPerformed
        ProxyFrame proxy_frame = new ProxyFrame();
        proxy_frame.setVisible(true);
        setVisible(false);
    }

    private void btnSysInfoActionPerformed(java.awt.event.ActionEvent evt) {//GEN-FIRST:event_btnSysInfoActionPerformed
        SystemInfoFrame systemInfo_frame = new SystemInfoFrame();
        systemInfo_frame.setVisible(true);
        setVisible(false);
    }

    private void btnTrModeActionPerformed(java.awt.event.ActionEvent evt) {//GEN-FIRST:event_btnTrModeActionPerformed
        TrModeFrame trMode_frame = new TrModeFrame();
        trMode_frame.setVisible(true);
        setVisible(false);
    }

    private void cmbMachineNumberMouseClicked(java.awt.event.MouseEvent evt) {
        SysUtil.MachineNumber = cmbMachineNumber.getSelectedIndex() + 1;
    }

    private void enableManagementGroup(boolean bEnable)
    {
        btnEnroll.setEnabled(bEnable);
        btnSysInfo.setEnabled(bEnable);
        btnLockControl.setEnabled(bEnable);
        btnBellTime.setEnabled(bEnable);
        btnTrMode.setEnabled(bEnable);
        btnProductCode.setEnabled(bEnable);
        btnAccessTz.setEnabled(bEnable);
        btnProxy.setEnabled(bEnable);
        btnDepartment.setEnabled(bEnable);
        btnLog.setEnabled(bEnable);
        
        btnClose.setEnabled(bEnable);
        btnOpen.setEnabled(!bEnable);
        
        optSerial.setEnabled(!bEnable);
        optNetwork.setEnabled(!bEnable);
        optViaP2P.setEnabled(!bEnable);
        
        cmbMachineNumber.setEnabled(!bEnable);
        
        refreshConnectMode(bEnable);
    }

    private boolean handleP2PResult(ConnectP2POutput output)
	{
		String title = "P2P Connection Result";
		if (output.success)
		{
			SysUtil.MachineNumber = output.devNo;
			if (output.error == 4)
				JOptionPane.showMessageDialog(null, "Relayed Connection!", title, JOptionPane.INFORMATION_MESSAGE);
			else if (output.error == 5)
				JOptionPane.showMessageDialog(null, "Direct Local Connection!", title, JOptionPane.INFORMATION_MESSAGE);
		}
		else
		{
			if (output.error == 1)
				JOptionPane.showMessageDialog(null, "Cannot Connect To Server!", title, JOptionPane.ERROR_MESSAGE);
			else if (output.error == 2)
				JOptionPane.showMessageDialog(null, "Device Not Found!", title, JOptionPane.ERROR_MESSAGE);
			else if (output.error == 3)
				JOptionPane.showMessageDialog(null, "Password Mismatched!", title, JOptionPane.ERROR_MESSAGE);
			else
				JOptionPane.showMessageDialog(null, "Unknown Error!", title, JOptionPane.ERROR_MESSAGE);
		}
		return output.success;
	}

    private void optNetworkStateChanged(javax.swing.event.ChangeEvent evt) {
        if(optNetwork.isSelected())
            switchConnectMode(ConnectMode.Network);
    }

    private void optSerialStateChanged(javax.swing.event.ChangeEvent evt) {
        if(optSerial.isSelected())
            ;//switchConnectMode(ConnectMode.Serial);
    }

    private void optViaP2PStateChanged(javax.swing.event.ChangeEvent evt) {//GEN-FIRST:event_optViaP2PStateChanged
        if(optViaP2P.isSelected())
            switchConnectMode(ConnectMode.viaP2P);
    }

    private void refreshConnectMode(boolean connected)
    {
    	if (connected)
    	{
    		cmbCommPort.setEnabled(false);
            cmbBaudrate.setEnabled(false);
            txtIPAddress.setEnabled(false);
            txtPortNumber.setEnabled(false);
            txtPassword.setEnabled(false);
            txtDeviceUID.setEnabled(false);
    	}
    	else
    	{
	    	if (optNetwork.isSelected())
	    		switchConnectMode(ConnectMode.Network);
	    	else
	    		switchConnectMode(ConnectMode.viaP2P);
    	}
    }

    private void switchConnectMode(ConnectMode mode)
    {
        txtIPAddress.setEnabled(mode == ConnectMode.Network || mode == ConnectMode.viaP2P);
        txtPortNumber.setEnabled(mode == ConnectMode.Network || mode == ConnectMode.viaP2P);
        txtPassword.setEnabled(mode == ConnectMode.Network || mode == ConnectMode.viaP2P);
        txtDeviceUID.setEnabled(mode == ConnectMode.viaP2P);
    }
}
