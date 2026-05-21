package smack.comm.sample;

import java.awt.EventQueue;
import java.awt.Font;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;

import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.SwingConstants;

import smack.comm.SBXPCProxy;
import smack.comm.output.OneLongOutput;
import smack.comm.sample.global.SysUtil;

import javax.swing.JButton;
import java.awt.event.ActionListener;
import java.awt.event.ActionEvent;

public class LockControlFrame extends JFrame {
	private JLabel lblMessage;
	private JButton btnGetDoorStatus;
	private JButton btnDoorOpen;
	private JButton btnUncondOpen;
	private JButton btnAutoRecover;
	private JButton btnUncondClose;
	private JButton btnReboot;
	private JButton btnWarnCancel;

	/**
	 * Launch the application.
	 */
	public static void main(String[] args) {
		EventQueue.invokeLater(new Runnable() {
			public void run() {
				try {
					LockControlFrame frame = new LockControlFrame();
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
	public LockControlFrame() {
		addWindowListener(new WindowAdapter() {
			@Override
			public void windowClosing(WindowEvent arg0) {
				if (MainFrame.getInstance() != null)
					MainFrame.getInstance().setVisible(true);
			}
		});
		
		setTitle("Lock Control");
		setBounds(100, 100, 438, 243);
		setDefaultCloseOperation(javax.swing.WindowConstants.DISPOSE_ON_CLOSE);
		getContentPane().setLayout(null);
		
		lblMessage = new JLabel("Message");
		lblMessage.setHorizontalAlignment(SwingConstants.CENTER);
		lblMessage.setFont(new Font("Segoe UI", Font.BOLD, 18));
		lblMessage.setBorder(javax.swing.BorderFactory.createBevelBorder(javax.swing.border.BevelBorder.LOWERED));
		lblMessage.setBounds(10, 11, 397, 45);
		getContentPane().add(lblMessage);
		
		btnGetDoorStatus = new JButton("Get DoorStatus");
		btnGetDoorStatus.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnGetDoorStatus_actionPerformed(arg0);
			}
		});
		btnGetDoorStatus.setBounds(10, 67, 126, 30);
		getContentPane().add(btnGetDoorStatus);
		
		btnDoorOpen = new JButton("Door Open");
		btnDoorOpen.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnDoorOpen_actionPerformed(arg0);				
			}
		});
		btnDoorOpen.setBounds(146, 67, 126, 30);
		getContentPane().add(btnDoorOpen);
		
		btnUncondOpen = new JButton("Uncond Open");
		btnUncondOpen.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnUncondOpen_actionPerformed(arg0);
			}
		});
		btnUncondOpen.setBounds(282, 67, 126, 30);
		getContentPane().add(btnUncondOpen);
		
		btnAutoRecover = new JButton("Auto Recover");
		btnAutoRecover.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnAutoRecover_actionPerformed(arg0);
			}
		});
		btnAutoRecover.setBounds(146, 110, 126, 30);
		getContentPane().add(btnAutoRecover);
		
		btnUncondClose = new JButton("Uncond Close");
		btnUncondClose.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnUncondClose_actionPerformed(arg0);
			}
		});
		btnUncondClose.setBounds(282, 110, 126, 30);
		getContentPane().add(btnUncondClose);
		
		btnReboot = new JButton("Reboot");
		btnReboot.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnReboot_actionPerformed(arg0);
			}
		});
		btnReboot.setBounds(146, 155, 126, 30);
		getContentPane().add(btnReboot);
		
		btnWarnCancel = new JButton("Warn Cancel");
		btnWarnCancel.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnWarnCancel_actionPerformed(arg0);
			}
		});
		btnWarnCancel.setBounds(282, 155, 126, 30);
		getContentPane().add(btnWarnCancel);

	}
	
	 private void btnGetDoorStatus_actionPerformed(ActionEvent evt) {//GEN-FIRST:event_btnGetDoorStatus_actionPerformed
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
	        
	        OneLongOutput output;
	        output = SBXPCProxy.GetDoorStatus(SysUtil.MachineNumber);
	        
	        if(output.isSuccess())
	        {
	            String message;
	            switch((int)output.dwValue)
	            {
	                case 1: message = "Uncond Door Open State";    break;
	                case 2: message = "Uncond Door Close State";   break;
	                case 3: message = "Door Open State";           break;
	                case 4: message = "Auto Recover State";        break;
	                case 5: message = "Door Close State";          break;
	                case 6: message = "Watching for Close";        break;
	                case 7: message = "Illegal open";              break;
	                default:message = "User State ";               break;
	            }
	            lblMessage.setText(message);
	            errorCode = 0;
	        }else
	        {
	            errorCode = (int)SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;
	            lblMessage.setText(SysUtil.ErrorPrint(errorCode));
	        }
	        
	        ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
	    }

	    private void btnDoorOpen_actionPerformed(ActionEvent evt) {
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
	        
	        ret = SBXPCProxy.SetDoorStatus(SysUtil.MachineNumber, 3);
	        if(ret)
	            errorCode = 0;
	        else
	            errorCode = (int)SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;
	        
	        lblMessage.setText(SysUtil.ErrorPrint(errorCode));
	        
	        ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
	    }

	    private void btnUncondOpen_actionPerformed(ActionEvent evt) {
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
	        
	        ret = SBXPCProxy.SetDoorStatus(SysUtil.MachineNumber, 1);
	        if(ret)
	            errorCode = 0;
	        else
	            errorCode = (int)SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;
	        
	        lblMessage.setText(SysUtil.ErrorPrint(errorCode));
	        
	        ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
	    }

	    private void btnAutoRecover_actionPerformed(ActionEvent evt) {
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
	        
	        ret = SBXPCProxy.SetDoorStatus(SysUtil.MachineNumber, 4);
	        if(ret)
	            errorCode = 0;
	        else
	            errorCode = (int)SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;
	        
	        lblMessage.setText(SysUtil.ErrorPrint(errorCode));
	        
	        ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
	    }
	    
	    private void btnUncondClose_actionPerformed(ActionEvent evt) {
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
	        
	        ret = SBXPCProxy.SetDoorStatus(SysUtil.MachineNumber, 2);
	        if(ret)
	            errorCode = 0;
	        else
	            errorCode = (int)SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;
	        
	        lblMessage.setText(SysUtil.ErrorPrint(errorCode));
	        
	        ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
	    }

	    private void btnReboot_actionPerformed(ActionEvent evt) {
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
	        
	        ret = SBXPCProxy.SetDoorStatus(SysUtil.MachineNumber, 5);
	        if(ret)
	            errorCode = 0;
	        else
	            errorCode = (int)SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;
	        
	        lblMessage.setText(SysUtil.ErrorPrint(errorCode));
	        
	        ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
	    }

	    private void btnWarnCancel_actionPerformed(ActionEvent evt) {
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
	        
	        ret = SBXPCProxy.SetDoorStatus(SysUtil.MachineNumber, 6);
	        if(ret)
	            errorCode = 0;
	        else
	            errorCode = (int)SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;
	        
	        lblMessage.setText(SysUtil.ErrorPrint(errorCode));
	        
	        ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
	    }
}
