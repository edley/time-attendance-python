package smack.comm.sample;

import java.awt.EventQueue;
import java.awt.Font;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;

import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JTextField;
import javax.swing.SwingConstants;

import smack.comm.SBXPCProxy;
import smack.comm.output.OneStringOutput;
import smack.comm.sample.global.SysUtil;

import javax.swing.JButton;
import java.awt.event.ActionListener;
import java.awt.event.ActionEvent;

public class ProductCodeFrame extends JFrame {
	private JLabel lblMessage;
	private JLabel lblSerialNumber;
	private JLabel lblBackupNumber;
	private JLabel lblProductCode;
	private JTextField txtSerialNumber;
	private JTextField txtBackupNumber;
	private JTextField txtProductCode;
	private JButton btnGetSerialNumber;
	private JButton btnGetBackupnumber;
	private JButton btnGetProductcode;

	/**
	 * Launch the application.
	 */
	public static void main(String[] args) {
		EventQueue.invokeLater(new Runnable() {
			public void run() {
				try {
					ProductCodeFrame frame = new ProductCodeFrame();
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
	public ProductCodeFrame() {
		addWindowListener(new WindowAdapter() {
			@Override
			public void windowClosing(WindowEvent arg0) {
				if (MainFrame.getInstance() != null)
					MainFrame.getInstance().setVisible(true);
			}
		});
	
		setTitle("Product Code");
		setBounds(100, 100, 388, 288);
		setDefaultCloseOperation(javax.swing.WindowConstants.DISPOSE_ON_CLOSE);
		getContentPane().setLayout(null);
		
		lblMessage = new JLabel("Message");
		lblMessage.setHorizontalAlignment(SwingConstants.CENTER);
		lblMessage.setFont(new Font("Segoe UI", Font.BOLD, 18));
		lblMessage.setBorder(javax.swing.BorderFactory.createBevelBorder(javax.swing.border.BevelBorder.LOWERED));
		lblMessage.setBounds(10, 11, 352, 40);
		getContentPane().add(lblMessage);
		
		lblSerialNumber = new JLabel("Serial Number: ");
		lblSerialNumber.setBounds(10, 64, 115, 14);
		getContentPane().add(lblSerialNumber);
		
		lblBackupNumber = new JLabel("Backup Number: ");
		lblBackupNumber.setBounds(10, 95, 115, 14);
		getContentPane().add(lblBackupNumber);
		
		lblProductCode = new JLabel("Product Code: ");
		lblProductCode.setBounds(10, 126, 115, 14);
		getContentPane().add(lblProductCode);
		
		txtSerialNumber = new JTextField();
		txtSerialNumber.setBounds(135, 64, 227, 20);
		getContentPane().add(txtSerialNumber);
		txtSerialNumber.setColumns(10);
		
		txtBackupNumber = new JTextField();
		txtBackupNumber.setBounds(135, 95, 227, 20);
		getContentPane().add(txtBackupNumber);
		txtBackupNumber.setColumns(10);
		
		txtProductCode = new JTextField();
		txtProductCode.setBounds(135, 126, 227, 20);
		getContentPane().add(txtProductCode);
		txtProductCode.setColumns(10);
		
		btnGetSerialNumber = new JButton("Get SerialNumber");
		btnGetSerialNumber.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnGetSerialNumber_actionPerformed(arg0);
			}
		});
		btnGetSerialNumber.setBounds(10, 164, 171, 28);
		getContentPane().add(btnGetSerialNumber);
		
		btnGetBackupnumber = new JButton("Get BackupNumber");
		btnGetBackupnumber.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnGetBackupNumber_actionPerformed(arg0);
			}
		});
		btnGetBackupnumber.setBounds(10, 203, 171, 28);
		getContentPane().add(btnGetBackupnumber);
		
		btnGetProductcode = new JButton("Get ProductCode");
		btnGetProductcode.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnGetProductCode_actionPerformed(arg0);
			}
		});
		btnGetProductcode.setBounds(191, 164, 171, 28);
		getContentPane().add(btnGetProductcode);
	}

	 private void btnGetSerialNumber_actionPerformed(ActionEvent evt) {
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
	        
	        OneStringOutput output;
	        output = SBXPCProxy.GetSerialNumber(SysUtil.MachineNumber);
	        
	        if(output.isSuccess())
	        {
	            txtSerialNumber.setText(output.value);
	            errorCode = 0;
	        }else
	        {
	            errorCode = (int)SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;
	        }
	        
	        lblMessage.setText(SysUtil.ErrorPrint(errorCode));
	        ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
	    }

	    private void btnGetBackupNumber_actionPerformed(ActionEvent evt) {
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
	        
	        long output;
	        output = SBXPCProxy.GetBackupNumber(SysUtil.MachineNumber);
	        
	        txtBackupNumber.setText(String.valueOf(output));
	        errorCode = 0;
	        
	        lblMessage.setText(SysUtil.ErrorPrint(errorCode));
	        ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
	    }

	    private void btnGetProductCode_actionPerformed(ActionEvent evt) {
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
	        
	        OneStringOutput output;
	        output = SBXPCProxy.GetProductCode(SysUtil.MachineNumber);
	        
	        if(output.isSuccess())
	        {
	            txtProductCode.setText(output.value);
	            errorCode = 0;
	        }else
	        {
	            errorCode = (int)SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;
	        }
	        
	        lblMessage.setText(SysUtil.ErrorPrint(errorCode));
	        ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
	    }
}
