package smack.comm.sample;

import java.awt.Color;
import java.awt.EventQueue;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.sql.SQLException;
import java.text.DecimalFormat;
import java.text.NumberFormat;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.logging.Level;
import java.util.logging.Logger;

import javax.swing.DefaultComboBoxModel;
import javax.swing.DefaultListModel;
import javax.swing.ImageIcon;
import javax.swing.JButton;
import javax.swing.JCheckBox;
import javax.swing.JComboBox;
import javax.swing.JFileChooser;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JList;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JTextField;
import javax.swing.SwingConstants;
import javax.swing.border.LineBorder;
import javax.swing.border.TitledBorder;

import smack.comm.SBXPCProxy;
import smack.comm.input.GetEnrollDataInput;
import smack.comm.input.GetUserNameInput;
import smack.comm.input.SetEnrollDataInput;
import smack.comm.input.SetUserNameInput;
import smack.comm.output.GetAllUserIDOutput;
import smack.comm.output.GetEnrollDataOutput;
import smack.comm.output.OneStringOutput;
import smack.comm.output.XMLParseBinaryByteOutput;
import smack.comm.sample.global.EnrollDBUtil;
import smack.comm.sample.global.SysUtil;
import smack.comm.sample.global.UserEnrollData;
import java.awt.Font;

public class EnrollMngFrame extends JFrame {
	/**
	 * Launch the application.
	 */
	public static void main(String[] args) {
		EventQueue.invokeLater(new Runnable() {
			public void run() {
				try {
					EnrollMngFrame frame = new EnrollMngFrame();
					frame.setVisible(true);
				} catch (Exception e) {
					e.printStackTrace();
				}
			}
		});
	}

	private JButton btnClearAllData;
	private JButton btnDeleteDb;
	private JButton btnDeleteEnrollData;
	private JButton btnDeleteUserPhoto;
	private JButton btnEmptyEnrollData;
	private JButton btnEnableUser;
	private JButton btnGetAllEnrollData;
	private JButton btnGetEnrollData;
	private JButton btnGetEnrollInfo;
	private JButton btnGetName;
	private JButton btnGetUserPhoto;
	private JButton btnModifyDuressFp;
	private JButton btnModifyPrivilege;
	private JButton btnRemoteEnrollCard;
	private JButton btnRemoteEnrollFace;
	private JButton btnRemoteEnrollFp;
	private JButton btnSetAllEnrollData;
	private JButton btnSetEnrollData;
	private JButton btnSetName;
	private JButton btnSetUserPhoto;
	private JButton btnUserPhotoBrowse;
	private JCheckBox chkDisableUser;
	private JCheckBox chkDupCheck;
	private JComboBox cmbBackupNumber;
	private JComboBox cmbDuress;
	private JComboBox cmbPrivilege;
	private JFileChooser fileChooserUserPhoto;
	private JLabel lblBackupNumber;
	private JLabel lblDepartment;
	private JLabel lblDisable;
	private JLabel lblDuress;
	private JLabel lblEnrollData;
	private JLabel lblEnrollNumber;
	private JLabel lblFaceFp;
	private JLabel lblMessage;
	private JLabel lblName;
	private JLabel lblPasswordCard;
	private JLabel lblPrivilege;
	private JLabel lblTotal;
	private JLabel lblUserPhoto;
	private JLabel lblUsertz_1;
	private JLabel lblUsertz_2;
	private JLabel lblUsertz_3;
	private JLabel lblUsertz_4;
	private JLabel lblUsertz_5;
	private JList lstEnrollData;
	private JPanel panelUserPhoto;
	private JTextField txtEnrollNum;
	private JTextField txtName;
	private JTextField txtPasswordCard;
	private JTextField txtUserDepart;
	private JTextField txtUserPhotoFile;
	private JTextField txtUserTz1;
	private JTextField txtUserTz2;
	private JTextField txtUserTz3;
	private JTextField txtUserTz4;
	private JTextField txtUserTz5;

	/**
	 * Create the frame.
	 */
	public EnrollMngFrame() {
		addWindowListener(new WindowAdapter() {
			@Override
			public void windowClosed(WindowEvent arg0) {
				if (MainFrame.getInstance() != null)
					MainFrame.getInstance().setVisible(true);
			}
		});

		setTitle("Enroll Management");
		setBounds(100, 100, 814, 500);
		setDefaultCloseOperation(javax.swing.WindowConstants.DISPOSE_ON_CLOSE);
		getContentPane().setLayout(null);

		lblEnrollNumber = new JLabel("Enroll Number :");
		lblEnrollNumber.setHorizontalAlignment(SwingConstants.RIGHT);
		lblEnrollNumber.setBounds(0, 63, 112, 14);
		getContentPane().add(lblEnrollNumber);

		txtEnrollNum = new JTextField();
		txtEnrollNum.setText("1");
		txtEnrollNum.setBounds(120, 60, 86, 20);
		getContentPane().add(txtEnrollNum);
		txtEnrollNum.setColumns(10);

		lblName = new JLabel("Name :");
		lblName.setHorizontalAlignment(SwingConstants.RIGHT);
		lblName.setBounds(0, 91, 112, 14);
		getContentPane().add(lblName);

		txtName = new JTextField();
		txtName.setColumns(10);
		txtName.setBounds(120, 88, 86, 20);
		getContentPane().add(txtName);

		lblDepartment = new JLabel("Depart No. :");
		lblDepartment.setHorizontalAlignment(SwingConstants.RIGHT);
		lblDepartment.setBounds(0, 116, 112, 14);
		getContentPane().add(lblDepartment);

		txtUserDepart = new JTextField();
		txtUserDepart.setColumns(10);
		txtUserDepart.setBounds(120, 113, 86, 20);
		getContentPane().add(txtUserDepart);

		lblPrivilege = new JLabel("Privilege :");
		lblPrivilege.setHorizontalAlignment(SwingConstants.RIGHT);
		lblPrivilege.setBounds(0, 141, 112, 14);
		getContentPane().add(lblPrivilege);

		cmbPrivilege = new JComboBox();
		cmbPrivilege.setModel(new DefaultComboBoxModel(new String[] { "0", "1", "2" }));
		cmbPrivilege.setBounds(120, 141, 86, 20);
		getContentPane().add(cmbPrivilege);

		lblFaceFp = new JLabel("0-9:fp,11:card,14:tz,15:pwd, 16:depart,17:face ");
		lblFaceFp.setBounds(58, 427, 311, 14);
		getContentPane().add(lblFaceFp);

		lblUsertz_1 = new JLabel("UserTz1 :");
		lblUsertz_1.setHorizontalAlignment(SwingConstants.RIGHT);
		lblUsertz_1.setBounds(0, 176, 112, 14);
		getContentPane().add(lblUsertz_1);

		txtUserTz1 = new JTextField();
		txtUserTz1.setColumns(10);
		txtUserTz1.setBounds(120, 173, 86, 20);
		getContentPane().add(txtUserTz1);

		lblUsertz_2 = new JLabel("UserTz2 :");
		lblUsertz_2.setHorizontalAlignment(SwingConstants.RIGHT);
		lblUsertz_2.setBounds(0, 198, 112, 14);
		getContentPane().add(lblUsertz_2);

		txtUserTz2 = new JTextField();
		txtUserTz2.setColumns(10);
		txtUserTz2.setBounds(120, 195, 86, 20);
		getContentPane().add(txtUserTz2);

		lblUsertz_3 = new JLabel("UserTz3 :");
		lblUsertz_3.setHorizontalAlignment(SwingConstants.RIGHT);
		lblUsertz_3.setBounds(0, 221, 112, 14);
		getContentPane().add(lblUsertz_3);

		txtUserTz3 = new JTextField();
		txtUserTz3.setColumns(10);
		txtUserTz3.setBounds(120, 218, 86, 20);
		getContentPane().add(txtUserTz3);

		lblUsertz_4 = new JLabel("UserTz4 :");
		lblUsertz_4.setHorizontalAlignment(SwingConstants.RIGHT);
		lblUsertz_4.setBounds(0, 243, 112, 14);
		getContentPane().add(lblUsertz_4);

		txtUserTz4 = new JTextField();
		txtUserTz4.setColumns(10);
		txtUserTz4.setBounds(120, 240, 86, 20);
		getContentPane().add(txtUserTz4);

		lblUsertz_5 = new JLabel("UserTz5 :");
		lblUsertz_5.setHorizontalAlignment(SwingConstants.RIGHT);
		lblUsertz_5.setBounds(0, 266, 112, 14);
		getContentPane().add(lblUsertz_5);

		txtUserTz5 = new JTextField();
		txtUserTz5.setColumns(10);
		txtUserTz5.setBounds(120, 263, 86, 20);
		getContentPane().add(txtUserTz5);

		lblDisable = new JLabel("Disable :");
		lblDisable.setHorizontalAlignment(SwingConstants.RIGHT);
		lblDisable.setBounds(0, 330, 112, 14);
		getContentPane().add(lblDisable);
		lblDisable.setLabelFor(chkDisableUser);

		chkDisableUser = new JCheckBox("");
		chkDisableUser.setToolTipText("");
		chkDisableUser.setBounds(120, 326, 21, 23);
		getContentPane().add(chkDisableUser);

		lblDuress = new JLabel("Duress :");
		lblDuress.setHorizontalAlignment(SwingConstants.RIGHT);
		lblDuress.setBounds(0, 304, 112, 14);
		getContentPane().add(lblDuress);

		cmbDuress = new JComboBox();
		cmbDuress.setModel(new DefaultComboBoxModel(new String[] { "0", "1" }));
		cmbDuress.setBounds(120, 301, 86, 20);
		getContentPane().add(cmbDuress);

		lblPasswordCard = new JLabel("Card / Password :");
		lblPasswordCard.setHorizontalAlignment(SwingConstants.RIGHT);
		lblPasswordCard.setBounds(0, 374, 112, 14);
		getContentPane().add(lblPasswordCard);

		txtPasswordCard = new JTextField();
		txtPasswordCard.setColumns(10);
		txtPasswordCard.setBounds(120, 371, 86, 20);
		getContentPane().add(txtPasswordCard);

		lblBackupNumber = new JLabel("Backup Number :");
		lblBackupNumber.setHorizontalAlignment(SwingConstants.RIGHT);
		lblBackupNumber.setBounds(0, 402, 112, 14);
		getContentPane().add(lblBackupNumber);

		cmbBackupNumber = new JComboBox();
		cmbBackupNumber.setModel(new DefaultComboBoxModel(
				new String[] { "0", "1", "2", "10", "11", "12", "13", "14", "15", "16", "17" }));
		cmbBackupNumber.setBounds(120, 402, 86, 20);
		getContentPane().add(cmbBackupNumber);

		lstEnrollData = new JList();
		lstEnrollData.setBorder(new LineBorder(new Color(0, 0, 0)));
		lstEnrollData.setBounds(241, 82, 197, 139);
		getContentPane().add(lstEnrollData);

		lblEnrollData = new JLabel("Enroll Data :");
		lblEnrollData.setBounds(241, 63, 112, 14);
		getContentPane().add(lblEnrollData);

		btnGetEnrollData = new JButton("Get EnrollData");
		btnGetEnrollData.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				boolean ret;
				int errorCode;

				lblMessage.setText(SysUtil.WORKING);
				invalidate();

				ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, false);

				if (!ret) {
					lblMessage.setText(SysUtil.NO_DEVICE);
					return;
				}

				GetEnrollDataInput input = new GetEnrollDataInput();
				input.dwMachineNumber = SysUtil.MachineNumber;
				input.dwEMachineNumber = SysUtil.MachineNumber;
				try {
					input.dwBackupNumber = Long.parseLong(cmbBackupNumber.getSelectedItem().toString());
					input.dwEnrollNumber = Long.parseLong(txtEnrollNum.getText());
				} catch (NumberFormatException ne) {
					ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
					JOptionPane.showMessageDialog(null, "Enroll number format is invalid.");
				}

				if (input.dwBackupNumber == 10)
					input.dwBackupNumber = 15;

				GetEnrollDataOutput output;

				output = SBXPCProxy.GetEnrollData(input);

				if (output.isSuccess()) {
					cmbPrivilege.setSelectedIndex((int) output.dwMachinePrivilege);

					if (input.dwBackupNumber == 11) // Card number
					{
						txtPasswordCard.setText(Long.toHexString(output.dwPassword));
					} else if (input.dwBackupNumber == 14) // User time zone
					{
						txtUserTz1.setText(String.valueOf(output.dwPassword % 64));
						output.dwPassword /= 64;
						txtUserTz2.setText(String.valueOf(output.dwPassword % 64));
						output.dwPassword /= 64;
						txtUserTz3.setText(String.valueOf(output.dwPassword % 64));
						output.dwPassword /= 64;
						txtUserTz4.setText(String.valueOf(output.dwPassword % 64));
						output.dwPassword /= 64;
						txtUserTz5.setText(String.valueOf(output.dwPassword % 64));
					} else if (input.dwBackupNumber == 15) // User password
					{
						String userPassword = "";
						while (output.dwPassword > 0) {
							userPassword += ((output.dwPassword & 0x0F) - 1);
							output.dwPassword /= 16;
						}
						txtPasswordCard.setText(userPassword);
					} else if (input.dwBackupNumber == 16) {
						txtUserDepart.setText(String.valueOf(output.dwPassword));
					} else {
						DefaultListModel model = new DefaultListModel();
						lstEnrollData.setModel(model);
						for (int i = 0; i < output.dwEnrollData.length; i++)
							model.addElement(output.dwEnrollData[i]);
					}
					errorCode = 0;
				} else {
					errorCode = (int) SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;
				}

				lblMessage.setText(SysUtil.ErrorPrint(errorCode));

				ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
			}
		});
		btnGetEnrollData.setBounds(459, 59, 149, 23);
		getContentPane().add(btnGetEnrollData);

		btnSetEnrollData = new JButton("Set EnrollData");
		btnSetEnrollData.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				boolean ret;
				int errorCode;

				lblMessage.setText(SysUtil.WORKING);
				invalidate();

				ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, false);

				if (!ret) {
					lblMessage.setText(SysUtil.NO_DEVICE);
					return;
				}

				SetEnrollDataInput input = new SetEnrollDataInput();
				input.dwMachineNumber = SysUtil.MachineNumber;
				input.dwEMachineNumber = SysUtil.MachineNumber;
				input.dwMachinePrivilege = cmbPrivilege.getSelectedIndex();
				try {
					input.dwBackupNumber = Long.parseLong(cmbBackupNumber.getSelectedItem().toString());
					input.dwEnrollNumber = Long.parseLong(txtEnrollNum.getText());
				} catch (NumberFormatException ne) {
					ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
					JOptionPane.showMessageDialog(null, "Enroll number format is invalid.");
				}

				if (input.dwBackupNumber == 10)
					input.dwBackupNumber = 15;

				if (input.dwBackupNumber == 11) // Card Number
				{
					try {
						input.dwPassword = Long.parseLong(txtPasswordCard.getText(), 16);
					} catch (NumberFormatException ne) {
						input.dwPassword = 0;
					}
				} else if (input.dwBackupNumber == 14) // User time zone
				{
					try {
						input.dwPassword = Long.parseLong(txtUserTz5.getText());
						input.dwPassword = input.dwPassword * 64 + Long.parseLong(txtUserTz4.getText());
						input.dwPassword = input.dwPassword * 64 + Long.parseLong(txtUserTz3.getText());
						input.dwPassword = input.dwPassword * 64 + Long.parseLong(txtUserTz2.getText());
						input.dwPassword = input.dwPassword * 64 + Long.parseLong(txtUserTz1.getText());
					} catch (NumberFormatException ne) {
						input.dwPassword = 0;
					}

				} else if (input.dwBackupNumber == 15) // User password
				{
					input.dwPassword = 0;
					String pwd = txtPasswordCard.getText();
					int i = Math.min(pwd.length(), 6);
					while (i > 0) {
						input.dwPassword = input.dwPassword * 16 + pwd.charAt(i - 1) - '0' + 1;
						i--;
					}
				} else if (input.dwBackupNumber == 16) // User department
				{
					try {
						input.dwPassword = Long.parseLong(txtUserDepart.getText());
					} catch (NumberFormatException ne) {
						input.dwPassword = 0;
					}
				} else {
					input.dwEnrollData = new int[lstEnrollData.getModel().getSize()];
					for (int i = 0; i < lstEnrollData.getModel().getSize(); i++)
						input.dwEnrollData[i] = Integer.parseInt(lstEnrollData.getModel().getElementAt(i).toString());
				}

				ret = SBXPCProxy.SetEnrollData(input);

				if (ret)
					errorCode = 0;
				else
					errorCode = (int) SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;

				lblMessage.setText(SysUtil.ErrorPrint(errorCode));

				ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);

			}
		});
		btnSetEnrollData.setBounds(618, 59, 149, 23);
		getContentPane().add(btnSetEnrollData);

		btnGetAllEnrollData = new JButton("Get All Enroll Data");
		btnGetAllEnrollData.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				boolean ret;
				int errorCode;

				lblMessage.setText(SysUtil.WORKING);
				invalidate();

				ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, false);

				if (!ret) {
					lblMessage.setText(SysUtil.NO_DEVICE);
					return;
				}

				ret = SBXPCProxy.ReadAllUserID(SysUtil.MachineNumber);

				if (ret) {
					errorCode = 0;

					int count = 0;
					GetAllUserIDOutput userIdOutput;
					GetEnrollDataInput enrollDataInput = new GetEnrollDataInput();
					GetEnrollDataOutput enrollDataOutput;
					UserEnrollData enrollData = new UserEnrollData();
					while (true) {
						userIdOutput = SBXPCProxy.GetAllUserID(SysUtil.MachineNumber);

						if (!userIdOutput.isSuccess())
							break;

						if (userIdOutput.dwBackupNumber >= 50)
							continue;

						enrollDataInput.dwMachineNumber = SysUtil.MachineNumber;
						enrollDataInput.dwEMachineNumber = SysUtil.MachineNumber;
						enrollDataInput.dwEnrollNumber = userIdOutput.dwEnrollNumber;
						enrollDataInput.dwBackupNumber = userIdOutput.dwBackupNumber;

						enrollDataOutput = SBXPCProxy.GetEnrollData(enrollDataInput);

						if (enrollDataOutput.isSuccess()) {
							enrollData.machineNo = (int) SysUtil.MachineNumber;
							enrollData.enrollNo = (int) enrollDataInput.dwEnrollNumber;
							enrollData.fingerNo = (int) enrollDataInput.dwBackupNumber;
							enrollData.password = (int) enrollDataOutput.dwPassword;
							enrollData.privilege = (int) enrollDataOutput.dwMachinePrivilege;
							enrollData.fpData = new int[enrollDataOutput.dwEnrollData.length];
							System.arraycopy(enrollDataOutput.dwEnrollData, 0, enrollData.fpData, 0,
									enrollDataOutput.dwEnrollData.length);
							try {
								EnrollDBUtil.updateEnrollData(enrollData);
								count++;
							} catch (SQLException se) {
								se.printStackTrace();
							}
						} else {
							errorCode = (int) SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;
							int selOpt = JOptionPane.showConfirmDialog(null, SysUtil.ErrorPrint(errorCode), "Continue?",
									JOptionPane.YES_NO_OPTION);
							if (selOpt == JOptionPane.NO_OPTION)
								break;
						}
					}
					lblTotal.setText("Total: " + count);
				} else
					errorCode = (int) SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;

				lblMessage.setText(SysUtil.ErrorPrint(errorCode));

				ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
			}
		});
		btnGetAllEnrollData.setBounds(459, 321, 149, 23);
		getContentPane().add(btnGetAllEnrollData);

		btnDeleteEnrollData = new JButton("Delete EnrollData");
		btnDeleteEnrollData.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				boolean ret;
				int errorCode;

				lblMessage.setText(SysUtil.WORKING);
				invalidate();

				ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, false);

				if (!ret) {
					lblMessage.setText(SysUtil.NO_DEVICE);
					return;
				}

				GetEnrollDataInput input = new GetEnrollDataInput();
				input.dwMachineNumber = SysUtil.MachineNumber;
				input.dwEMachineNumber = SysUtil.MachineNumber;
				try {
					input.dwBackupNumber = Long.parseLong(cmbBackupNumber.getSelectedItem().toString());
					input.dwEnrollNumber = Long.parseLong(txtEnrollNum.getText());
				} catch (NumberFormatException ne) {
					ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
					JOptionPane.showMessageDialog(null, "Enroll number format is invalid.");
				}

				if (input.dwBackupNumber == 10)
					input.dwBackupNumber = 15;

				ret = SBXPCProxy.DeleteEnrollData(input);

				if (ret)
					errorCode = 0;
				else
					errorCode = (int) SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;

				lblMessage.setText(SysUtil.ErrorPrint(errorCode));

				ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
			}
		});
		btnDeleteEnrollData.setBounds(459, 85, 149, 23);
		getContentPane().add(btnDeleteEnrollData);

		chkDupCheck = new JCheckBox("FP duplication check");
		chkDupCheck.setBounds(631, 297, 136, 23);
		getContentPane().add(chkDupCheck);

		btnGetName = new JButton("Get Name");
		btnGetName.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				boolean ret;
				int errorCode;

				lblMessage.setText(SysUtil.WORKING);
				invalidate();

				ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, false);

				if (!ret) {
					lblMessage.setText(SysUtil.NO_DEVICE);
					return;
				}

				GetUserNameInput input = new GetUserNameInput();
				input.dwMachineNumber = SysUtil.MachineNumber;
				try {
					input.dwEnrollNumber = Long.parseLong(txtEnrollNum.getText());
				} catch (NumberFormatException ne) {
					input.dwEnrollNumber = 1;
					txtEnrollNum.setText("1");
				}

				OneStringOutput output;
				output = SBXPCProxy.GetUserName(input);

				if (output.isSuccess()) {
					errorCode = 0;
					txtName.setText(output.value);
				} else
					errorCode = (int) SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;

				lblMessage.setText(SysUtil.ErrorPrint(errorCode));

				ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
			}
		});
		btnGetName.setBounds(459, 113, 149, 23);
		getContentPane().add(btnGetName);

		btnSetName = new JButton("Set Name");
		btnSetName.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				boolean ret;
				int errorCode;

				lblMessage.setText(SysUtil.WORKING);
				invalidate();

				ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, false);

				if (!ret) {
					lblMessage.setText(SysUtil.NO_DEVICE);
					return;
				}

				SetUserNameInput input = new SetUserNameInput();
				input.dwMachineNumber = SysUtil.MachineNumber;
				input.setUserName(txtName.getText());
				try {
					input.dwEnrollNumber = Long.parseLong(txtEnrollNum.getText());
				} catch (NumberFormatException ne) {
					input.dwEnrollNumber = 1;
					txtEnrollNum.setText("0");
				}

				ret = SBXPCProxy.SetUserName(input);

				if (ret)
					errorCode = 0;
				else
					errorCode = (int) SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;

				lblMessage.setText(SysUtil.ErrorPrint(errorCode));

				ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
			}
		});
		btnSetName.setBounds(618, 113, 149, 23);
		getContentPane().add(btnSetName);

		btnGetEnrollInfo = new JButton("Get Enroll Info");
		btnGetEnrollInfo.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				boolean ret;
				int errorCode;

				lblMessage.setText(SysUtil.WORKING);
				invalidate();

				ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, false);

				if (!ret) {
					lblMessage.setText(SysUtil.NO_DEVICE);
					return;
				}

				ret = SBXPCProxy.ReadAllUserID(SysUtil.MachineNumber);

				if (ret) {
					errorCode = 0;
					GetAllUserIDOutput output;
					String element = "No.    EnNo   EMNo   Fp   Priv  Enable Duress";
					DefaultListModel listModel = new DefaultListModel();
					listModel.addElement(element);

					NumberFormat format2 = new DecimalFormat("00");
					NumberFormat format3 = new DecimalFormat("000");
					NumberFormat format5 = new DecimalFormat("00000");
					int count = 0;
					while (true) {
						output = SBXPCProxy.GetAllUserID(SysUtil.MachineNumber);
						if (!output.isSuccess())
							break;
						element = format3.format(count) + "   ";
						element += format5.format(output.dwEnrollNumber) + "    ";
						element += format3.format(output.dwEMachineNumber) + "      ";
						element += format2.format(output.dwBackupNumber) + "    ";
						element += String.valueOf(output.dwMachinePrivilege) + "        ";
						element += String.valueOf(output.dwEnable % 256) + "        ";
						element += String.valueOf(output.dwEnable / 256);

						listModel.addElement(element);

						count++;
					}
					lstEnrollData.setModel(listModel);
					lblTotal.setText("Total: " + count);
				} else
					errorCode = (int) SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;

				lblMessage.setText(SysUtil.ErrorPrint(errorCode));

				ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
			}
		});
		btnGetEnrollInfo.setBounds(459, 353, 149, 23);
		getContentPane().add(btnGetEnrollInfo);

		btnEnableUser = new JButton("Enable User");
		btnEnableUser.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				boolean ret;
				int errorCode;

				lblMessage.setText(SysUtil.WORKING);
				invalidate();

				ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, false);

				if (!ret) {
					lblMessage.setText(SysUtil.NO_DEVICE);
					return;
				}

				GetEnrollDataInput input = new GetEnrollDataInput();
				input.dwMachineNumber = SysUtil.MachineNumber;
				input.dwEMachineNumber = SysUtil.MachineNumber;
				try {
					input.dwEnrollNumber = Long.parseLong(txtEnrollNum.getText());
					input.dwBackupNumber = Long.parseLong(cmbBackupNumber.getSelectedItem().toString());
				} catch (NumberFormatException ne) {
					input.dwEnrollNumber = 1;
					txtEnrollNum.setText("1");
					input.dwBackupNumber = 0;
					cmbBackupNumber.setSelectedIndex(0);
				}

				ret = SBXPCProxy.EnableUser(input, !chkDisableUser.isSelected());

				if (ret)
					errorCode = 0;
				else
					errorCode = (int) SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;

				lblMessage.setText(SysUtil.ErrorPrint(errorCode));

				ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
			}
		});
		btnEnableUser.setBounds(459, 198, 149, 23);
		getContentPane().add(btnEnableUser);

		btnModifyPrivilege = new JButton("Modify Privilege");
		btnModifyPrivilege.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				boolean ret;
				int errorCode;

				lblMessage.setText(SysUtil.WORKING);
				invalidate();

				ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, false);

				if (!ret) {
					lblMessage.setText(SysUtil.NO_DEVICE);
					return;
				}

				GetEnrollDataInput input = new GetEnrollDataInput();
				input.dwMachineNumber = SysUtil.MachineNumber;
				input.dwEMachineNumber = SysUtil.MachineNumber;
				try {
					input.dwEnrollNumber = Long.parseLong(txtEnrollNum.getText());
					input.dwBackupNumber = Long.parseLong(cmbBackupNumber.getSelectedItem().toString());
				} catch (NumberFormatException ne) {
					input.dwEnrollNumber = 1;
					txtEnrollNum.setText("1");
					input.dwBackupNumber = 0;
					cmbBackupNumber.setSelectedIndex(0);
				}

				ret = SBXPCProxy.ModifyPrivilege(input, cmbPrivilege.getSelectedIndex());

				if (ret)
					errorCode = 0;
				else
					errorCode = (int) SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;

				lblMessage.setText(SysUtil.ErrorPrint(errorCode));

				ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
			}
		});
		btnModifyPrivilege.setBounds(459, 147, 149, 23);
		getContentPane().add(btnModifyPrivilege);

		btnModifyDuressFp = new JButton("Modify Duress FP");
		btnModifyDuressFp.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				boolean ret;
				int errorCode;

				lblMessage.setText(SysUtil.WORKING);
				invalidate();

				ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, false);

				if (!ret) {
					lblMessage.setText(SysUtil.NO_DEVICE);
					return;
				}

				long dwEnrollNumber;
				long dwBackupNumber;
				try {
					dwEnrollNumber = Long.parseLong(txtEnrollNum.getText());
					dwBackupNumber = Long.parseLong(cmbBackupNumber.getSelectedItem().toString());
				} catch (NumberFormatException ne) {
					dwEnrollNumber = 1;
					txtEnrollNum.setText("1");
					dwBackupNumber = 0;
					cmbBackupNumber.setSelectedIndex(0);
				}

				ret = SBXPCProxy.ModifyDuressFP(SysUtil.MachineNumber, dwEnrollNumber, dwBackupNumber,
						cmbDuress.getSelectedIndex());

				if (ret)
					errorCode = 0;
				else
					errorCode = (int) SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;

				lblMessage.setText(SysUtil.ErrorPrint(errorCode));

				ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
			}
		});
		btnModifyDuressFp.setBounds(459, 172, 149, 23);
		getContentPane().add(btnModifyDuressFp);

		btnRemoteEnrollFace = new JButton("Remote Enroll Face");
		btnRemoteEnrollFace.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				RemoteEnroll_actionPerformed(arg0, "RemoteEnrollFace");
			}
		});
		btnRemoteEnrollFace.setBounds(618, 147, 149, 23);
		getContentPane().add(btnRemoteEnrollFace);

		btnRemoteEnrollFp = new JButton("Remote Enroll FP");
		btnRemoteEnrollFp.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				RemoteEnroll_actionPerformed(arg0, "RemoteEnrollFP");
			}
		});
		btnRemoteEnrollFp.setBounds(618, 172, 149, 23);
		getContentPane().add(btnRemoteEnrollFp);

		btnRemoteEnrollCard = new JButton("Remote Enroll Card");
		btnRemoteEnrollCard.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				RemoteEnroll_actionPerformed(arg0, "RemoteEnrollCard");
			}
		});
		btnRemoteEnrollCard.setBounds(618, 198, 149, 23);
		getContentPane().add(btnRemoteEnrollCard);

		btnEmptyEnrollData = new JButton("Empty Enroll Data");
		btnEmptyEnrollData.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				boolean ret;
				int errorCode;

				lblMessage.setText(SysUtil.WORKING);
				invalidate();

				ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, false);

				if (!ret) {
					lblMessage.setText(SysUtil.NO_DEVICE);
					return;
				}

				ret = SBXPCProxy.EmptyEnrollData(SysUtil.MachineNumber);

				if (ret)
					errorCode = 0;
				else
					errorCode = (int) SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;

				lblMessage.setText(SysUtil.ErrorPrint(errorCode));

				ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
			}
		});
		btnEmptyEnrollData.setBounds(618, 353, 149, 23);
		getContentPane().add(btnEmptyEnrollData);

		btnClearAllData = new JButton("Clear All Data(E, GL, SL)");
		btnClearAllData.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				boolean ret;
				int errorCode;

				lblMessage.setText(SysUtil.WORKING);
				invalidate();

				ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, false);

				if (!ret) {
					lblMessage.setText(SysUtil.NO_DEVICE);
					return;
				}

				ret = SBXPCProxy.ClearKeeperData(SysUtil.MachineNumber);

				if (ret)
					errorCode = 0;
				else
					errorCode = (int) SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;

				lblMessage.setText(SysUtil.ErrorPrint(errorCode));

				ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
			}
		});
		btnClearAllData.setBounds(459, 398, 149, 23);
		getContentPane().add(btnClearAllData);

		btnDeleteDb = new JButton("Delete DB");
		btnDeleteDb.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				try {
					EnrollDBUtil.deleteAllEnrollData(SysUtil.MachineNumber);
					lblTotal.setText("Total: 0");
					lblMessage.setText("Delete DB Success.");
				} catch (SQLException ex) {
					Logger.getLogger(EnrollMngFrame.class.getName()).log(Level.SEVERE, null, ex);
				}
			}
		});
		btnDeleteDb.setBounds(618, 401, 149, 23);
		getContentPane().add(btnDeleteDb);

		lblMessage = new JLabel("Message");
		lblMessage.setHorizontalAlignment(SwingConstants.CENTER);
		lblMessage.setFont(new Font("Segoe UI", Font.BOLD, 18));
		lblMessage.setBorder(javax.swing.BorderFactory.createBevelBorder(javax.swing.border.BevelBorder.LOWERED));
		lblMessage.setBounds(27, 13, 740, 37);
		getContentPane().add(lblMessage);

		lblTotal = new JLabel("Total :");
		lblTotal.setHorizontalAlignment(SwingConstants.LEFT);
		lblTotal.setBounds(496, 301, 112, 14);
		getContentPane().add(lblTotal);

		panelUserPhoto = new JPanel();
		panelUserPhoto
				.setBorder(new TitledBorder(null, "UserPhoto", TitledBorder.LEADING, TitledBorder.TOP, null, null));
		panelUserPhoto.setBounds(241, 236, 197, 188);
		getContentPane().add(panelUserPhoto);
		panelUserPhoto.setLayout(null);

		txtUserPhotoFile = new JTextField();
		txtUserPhotoFile.setBounds(12, 155, 143, 20);
		panelUserPhoto.add(txtUserPhotoFile);
		txtUserPhotoFile.setColumns(10);

		fileChooserUserPhoto = new javax.swing.JFileChooser();
		btnUserPhotoBrowse = new JButton("...");
		btnUserPhotoBrowse.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				fileChooserUserPhoto.showOpenDialog(null);
				File selectedFile = fileChooserUserPhoto.getSelectedFile();

				if (selectedFile == null)
					return;
				txtUserPhotoFile.setText(selectedFile.getPath());

				lblUserPhoto.setIcon(new ImageIcon(txtUserPhotoFile.getText()));
			}
		});
		btnUserPhotoBrowse.setBounds(158, 154, 24, 21);
		panelUserPhoto.add(btnUserPhotoBrowse);

		lblUserPhoto = new JLabel("");
		lblUserPhoto.setBorder(javax.swing.BorderFactory.createBevelBorder(javax.swing.border.BevelBorder.LOWERED));
		lblUserPhoto.setBounds(12, 21, 170, 130);
		panelUserPhoto.add(lblUserPhoto);

		btnGetUserPhoto = new JButton("Get User Photo");
		btnGetUserPhoto.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				boolean ret;
				int errorCode;

				lblMessage.setText(SysUtil.WORKING);
				invalidate();

				ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, false);

				if (!ret) {
					lblMessage.setText(SysUtil.NO_DEVICE);
					return;
				}

				lblUserPhoto.setIcon(null);
				txtUserPhotoFile.setText("");

				long userId;
				try {
					userId = Long.parseLong(txtEnrollNum.getText());
				} catch (NumberFormatException ne) {
					userId = 0;
				}

				OneStringOutput output;
				output = SysUtil.MakeXMLCommandHeader("GetUserPhotoData");
				output = SBXPCProxy.XML_AddLong(output.value, "UserID", userId);

				output = SBXPCProxy.GeneralOperationXML(SysUtil.MachineNumber, output.value);

				if (output.isSuccess()) {
					XMLParseBinaryByteOutput parseOutput;
					parseOutput = SBXPCProxy.XML_ParseBinaryByte(output.value, "PhotoData",
							SysUtil.COMPRESSED_PHOTO_SIZE);
					if (parseOutput.isSuccess())
						lblUserPhoto.setIcon(new ImageIcon(parseOutput.pData));
					errorCode = 0;
				} else
					errorCode = (int) SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;

				lblMessage.setText(SysUtil.ErrorPrint(errorCode));

				ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
			}
		});
		btnGetUserPhoto.setBounds(459, 238, 149, 23);
		getContentPane().add(btnGetUserPhoto);

		btnSetUserPhoto = new JButton("Set User Photo");
		btnSetUserPhoto.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				long userId;
				try {
					userId = Long.parseLong(txtEnrollNum.getText());
				} catch (NumberFormatException ne) {
					JOptionPane.showMessageDialog(null, "Invalid Enroll Number");
					return;
				}

				byte[] userPhotoData;
				int PhotoSize = 0;

				FileInputStream fis = null;
				try {
					fis = new FileInputStream(txtUserPhotoFile.getText());
					PhotoSize = fis.available();
					if (PhotoSize > SysUtil.COMPRESSED_PHOTO_SIZE)
						return;
					userPhotoData = new byte[PhotoSize];
					fis.read(userPhotoData);
				} catch (IOException ex) {
					JOptionPane.showMessageDialog(null, "Invalid user photo file.");
					return;
				} finally {
					if (fis != null) {
						try {
							fis.close();
						} catch (IOException ex) {
						}
					}
				}

				boolean ret;
				int errorCode;

				lblMessage.setText(SysUtil.WORKING);
				invalidate();

				ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, false);

				if (!ret) {
					lblMessage.setText(SysUtil.NO_DEVICE);
					return;
				}

				OneStringOutput output;
				output = SysUtil.MakeXMLCommandHeader("SetUserPhotoData");
				output = SBXPCProxy.XML_AddLong(output.value, "UserID", userId);
				output = SBXPCProxy.XML_AddLong(output.value, "PhotoSize", PhotoSize);
				output = SBXPCProxy.XML_AddBinaryByte(output.value, "PhotoData", userPhotoData, PhotoSize);

				output = SBXPCProxy.GeneralOperationXML(SysUtil.MachineNumber, output.value);

				if (output.isSuccess())
					errorCode = 0;
				else
					errorCode = (int) SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;

				lblMessage.setText(SysUtil.ErrorPrint(errorCode));

				ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
			}
		});
		btnSetUserPhoto.setBounds(618, 238, 149, 23);
		getContentPane().add(btnSetUserPhoto);

		btnDeleteUserPhoto = new JButton("Delete User Photo");
		btnDeleteUserPhoto.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				long userId;
				try {
					userId = Long.parseLong(txtEnrollNum.getText());
				} catch (NumberFormatException ne) {
					return;
				}

				boolean ret;
				int errorCode;

				lblMessage.setText(SysUtil.WORKING);
				invalidate();

				ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, false);

				if (!ret) {
					lblMessage.setText(SysUtil.NO_DEVICE);
					return;
				}

				OneStringOutput output;
				output = SysUtil.MakeXMLCommandHeader("SetUserPhotoData");
				output = SBXPCProxy.XML_AddLong(output.value, "UserID", userId);
				// Did not set "PhotoData" field to delete user photo

				output = SBXPCProxy.GeneralOperationXML(SysUtil.MachineNumber, output.value);

				if (output.isSuccess())
					errorCode = 0;
				else
					errorCode = (int) SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;

				lblMessage.setText(SysUtil.ErrorPrint(errorCode));

				ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
			}
		});
		btnDeleteUserPhoto.setBounds(618, 263, 149, 23);
		getContentPane().add(btnDeleteUserPhoto);

		btnSetAllEnrollData = new JButton("Set All Enroll Data");
		btnSetAllEnrollData.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				List<UserEnrollData> enrollDataList = new ArrayList<UserEnrollData>();
				try {
					EnrollDBUtil.getAllEnrollData(SysUtil.MachineNumber, enrollDataList);
				} catch (SQLException ex) {
					Logger.getLogger(EnrollMngFrame.class.getName()).log(Level.SEVERE, null, ex);
					return;
				}

				boolean ret;
				int errorCode = 0;

				lblMessage.setText(SysUtil.WORKING);
				invalidate();

				ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, false);

				if (!ret) {
					lblMessage.setText(SysUtil.NO_DEVICE);
					return;
				}

				Iterator<UserEnrollData> iter = enrollDataList.iterator();
				UserEnrollData enrollData;
				SetEnrollDataInput input;
				while (iter.hasNext()) {
					input = new SetEnrollDataInput();
					enrollData = iter.next();
					input.dwMachineNumber = enrollData.machineNo;
					input.dwEMachineNumber = enrollData.machineNo;
					input.dwEnrollNumber = enrollData.enrollNo;
					input.dwBackupNumber = enrollData.fingerNo;
					input.dwMachinePrivilege = enrollData.privilege;
					input.dwPassword = enrollData.password;
					input.dwEnrollData = enrollData.fpData;

					if (input.dwBackupNumber >= 0 && input.dwBackupNumber <= 9 && !chkDupCheck.isSelected())
						input.dwBackupNumber = input.dwBackupNumber + 20;

					ret = SBXPCProxy.SetEnrollData(input);

					if (ret)
						errorCode = 0;
					else
						errorCode = (int) SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;
				}

				lblMessage.setText(SysUtil.ErrorPrint(errorCode));

				ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
			}
		});
		btnSetAllEnrollData.setBounds(618, 321, 149, 23);
		getContentPane().add(btnSetAllEnrollData);

	}

	public void RemoteEnroll_actionPerformed(ActionEvent arg0, String Backup) {
		long userId;
		try {
			userId = Long.parseLong(txtEnrollNum.getText());
		} catch (NumberFormatException ne) {
			JOptionPane.showMessageDialog(null, "Invalid Enroll Number");
			return;
		}

		lblMessage.setText(SysUtil.WORKING);
		invalidate();

		int errorCode;
		OneStringOutput output;
		output = SysUtil.MakeXMLCommandHeader("RemoteEnroll");
		output = SBXPCProxy.XML_AddLong(output.value, "UserID", userId);
		output = SBXPCProxy.XML_AddString(output.value, "Backup", Backup);

		output = SBXPCProxy.GeneralOperationXML(SysUtil.MachineNumber, output.value);

		if (output.isSuccess()) {
			String strResultCode = SBXPCProxy.XML_ParseString(output.value, "ResultCode").value;
			if (strResultCode.equals("MenuProcessing"))
				lblMessage.setText("Machine is now processing menu.");
			else if (strResultCode.equals("InvalidBackup"))
				lblMessage.setText("Invalid Remote Enroll Backup");
			else if (strResultCode.equals("EnrollNumberError"))
				lblMessage.setText("Invalid Enroll Number");
			else if (strResultCode.equals("FaceAlreadyEnrolled"))
				lblMessage.setText("Face already are enrolled for this user");
			else if (strResultCode.equals("FPAllEnrolled"))
				lblMessage.setText("All fingerprints are enrolled for this user");
			else if (strResultCode.equals("CardAlreadyEnrolled"))
				lblMessage.setText("Card already are enrolled for this user");
			else if (strResultCode.equals("DatabaseFull"))
				lblMessage.setText("Fingerprint database is full.");
			else if (strResultCode.equals("RemoteEnrollAlreadyStarted"))
				lblMessage.setText("Remote Enroll Already Started.");
			else if (strResultCode.equals("Success"))
				lblMessage.setText("Remote Enroll Started.");
			else
				lblMessage.setText("Unknown Error");
		} else {
			errorCode = (int) SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;
			lblMessage.setText(SysUtil.ErrorPrint(errorCode));
		}
	}

}
