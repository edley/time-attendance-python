package smack.comm.sample;

import java.awt.Color;
import java.awt.Cursor;
import java.awt.EventQueue;
import java.awt.Font;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.text.DecimalFormat;
import java.text.NumberFormat;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Date;
import java.util.List;

import javax.swing.ImageIcon;
import javax.swing.JButton;
import javax.swing.JCheckBox;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTable;
import javax.swing.JTextField;
import javax.swing.SwingConstants;
import javax.swing.UIManager;
import javax.swing.border.BevelBorder;
import javax.swing.border.TitledBorder;
import javax.swing.table.AbstractTableModel;

import smack.comm.SBXPCProxy;
import smack.comm.data.GeneralLogData;
import smack.comm.data.SuperLogData;
import smack.comm.output.GeneralLogDataOutput;
import smack.comm.output.OneStringOutput;
import smack.comm.output.SuperLogDataOutput;
import smack.comm.output.XMLParseBinaryByteOutput;
import smack.comm.sample.global.SysUtil;
import java.awt.event.ActionListener;
import java.awt.event.ActionEvent;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.awt.GridLayout;

public class LogMngFrame extends JFrame {
	private JLabel lblMessage;
	private JLabel lblLogData;
	private JLabel lblTotal;
	private JTable tblLogList;
	private JScrollPane jScrollPane1;
	private JCheckBox chkSearchAndDelete;
	private JCheckBox chkReadMark;
	private JCheckBox chkShowGLogPhoto;
	private JLabel lblGLogPhoto;
	private JButton btnDeleteGLogPhoto;
	private JButton btnReadSLogData;
	private JButton btnReadAllSLogData;
	private JButton btnEmptySLogData;
	private JButton btnReadGLogData;
	private JButton btnReadAllGLogData;
	private JButton btnEmptyGLogData;

	SLogDataListModel superLogListModel = new SLogDataListModel();
	GLogDataListModel generalLogListMOdel = new GLogDataListModel();

	private int prevSelectedRow = -1;
	private JPanel panel_2;

	/**
	 * Launch the application.
	 */
	public static void main(String[] args) {
		EventQueue.invokeLater(new Runnable() {
			public void run() {
				try {
					LogMngFrame frame = new LogMngFrame();
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
	public LogMngFrame() {
		addWindowListener(new WindowAdapter() {
			@Override
			public void windowClosing(WindowEvent arg0) {
				if (MainFrame.getInstance() != null)
					MainFrame.getInstance().setVisible(true);
			}
		});

		setTitle("Log Management");
		setBounds(100, 100, 823, 669);
		setDefaultCloseOperation(javax.swing.WindowConstants.DISPOSE_ON_CLOSE);
		getContentPane().setLayout(null);

		lblMessage = new JLabel("Message");
		lblMessage.setHorizontalAlignment(SwingConstants.CENTER);
		lblMessage.setFont(new Font("Segoe UI", Font.BOLD, 18));
		lblMessage.setBorder(javax.swing.BorderFactory.createBevelBorder(javax.swing.border.BevelBorder.LOWERED));
		lblMessage.setBounds(10, 11, 637, 32);
		getContentPane().add(lblMessage);

		lblLogData = new JLabel("Log Data ");
		lblLogData.setBounds(10, 54, 70, 14);
		getContentPane().add(lblLogData);

		lblTotal = new JLabel("Total :");
		lblTotal.setBounds(145, 54, 157, 14);
		getContentPane().add(lblTotal);

		jScrollPane1 = new JScrollPane();
		jScrollPane1.setBounds(10, 79, 637, 459);
		getContentPane().add(jScrollPane1);

		tblLogList = new JTable();
		tblLogList.addMouseListener(new MouseAdapter() {
			@Override
			public void mouseClicked(MouseEvent arg0) {
				tblLogListMouseClicked(arg0);
			}
		});
		jScrollPane1.setViewportView(tblLogList);

		chkSearchAndDelete = new JCheckBox("and Delete");
		chkSearchAndDelete.setBounds(451, 50, 97, 23);
		getContentPane().add(chkSearchAndDelete);

		chkReadMark = new JCheckBox("ReadMark");
		chkReadMark.setSelected(true);
		chkReadMark.setBounds(550, 50, 97, 23);
		getContentPane().add(chkReadMark);

		chkShowGLogPhoto = new JCheckBox("Show GLog Photo");
		chkShowGLogPhoto.setSelected(true);
		chkShowGLogPhoto.setBounds(668, 79, 125, 23);
		getContentPane().add(chkShowGLogPhoto);

		lblGLogPhoto = new JLabel("");
		lblGLogPhoto.setBorder(new BevelBorder(BevelBorder.LOWERED, null, null, null, null));
		lblGLogPhoto.setBounds(657, 109, 139, 143);
		getContentPane().add(lblGLogPhoto);

		btnDeleteGLogPhoto = new JButton("DeleteGLogPhoto");
		btnDeleteGLogPhoto.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnDeleteGLogPhoto_actionPerformed(arg0);
			}
		});
		btnDeleteGLogPhoto.setBounds(657, 263, 136, 34);
		getContentPane().add(btnDeleteGLogPhoto);

		panel_2 = new JPanel();
		panel_2.setBorder(
				new TitledBorder(UIManager.getBorder("TitledBorder.border"), "", TitledBorder.LEADING, TitledBorder.TOP, null, new Color(0, 0, 0)));
		panel_2.setBounds(10, 549, 637, 70);
		getContentPane().add(panel_2);
		panel_2.setLayout(new GridLayout(0, 6, 0, 0));

		btnReadSLogData = new JButton("<html>Read<br>SLog Data</html>");
		panel_2.add(btnReadSLogData);

		btnReadAllSLogData = new JButton("<html>Read All<br>SLog Data</html>");
		panel_2.add(btnReadAllSLogData);

		btnEmptySLogData = new JButton("<html>Empty<br>SLog Data</html>");
		panel_2.add(btnEmptySLogData);

		btnReadGLogData = new JButton("<html>Read<br>GLog Data</html>");
		panel_2.add(btnReadGLogData);

		btnReadAllGLogData = new JButton("<html>Read All<br>GLog Data</html>");
		panel_2.add(btnReadAllGLogData);

		btnEmptyGLogData = new JButton("<html>Empty<br>GLog Data</html>");
		panel_2.add(btnEmptyGLogData);
		btnEmptyGLogData.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnEmptyGLogData_actionPerformed(arg0);
			}
		});
		btnReadAllGLogData.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnReadAllGLogData_actionPerformed(arg0);
			}
		});
		btnReadGLogData.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnReadGLogData_actionPerformed(arg0);
			}
		});
		btnEmptySLogData.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnEmptySLogData_actionPerformed(arg0);
			}
		});
		btnReadAllSLogData.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnReadAllSLogData_actionPerformed(arg0);
			}
		});
		btnReadSLogData.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnReadSLogData_actionPerformed(arg0);
			}
		});
	}

	private void btnReadSLogData_actionPerformed(ActionEvent evt) {
		superLogListModel.removeAll();
		tblLogList.setModel(superLogListModel);

		boolean ret;
		int errorCode;

		lblMessage.setText(SysUtil.WORKING);
		invalidate();

		ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, false);

		if (!ret) {
			lblMessage.setText(SysUtil.NO_DEVICE);
			return;
		}

		ret = SBXPCProxy.ReadSuperLogData(SysUtil.MachineNumber, chkReadMark.isSelected());

		if (ret) {
			errorCode = 0;

			if (chkSearchAndDelete.isSelected())
				ret = SBXPCProxy.EmptySuperLogData(SysUtil.MachineNumber);

			lblMessage.setText("Getting...");
			invalidate();

			SuperLogDataOutput output;
			while (true) {
				output = SBXPCProxy.GetSuperLogData(SysUtil.MachineNumber);

				if (!output.isSuccess())
					break;

				superLogListModel.addSLogData(output);
			}
			lblTotal.setText("Total: " + superLogListModel.getRowCount());
		} else {
			errorCode = (int) SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;
		}

		lblMessage.setText(SysUtil.ErrorPrint(errorCode));

		ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);

	}

	private void btnReadAllSLogData_actionPerformed(ActionEvent evt) {
		superLogListModel.removeAll();
		tblLogList.setModel(superLogListModel);

		boolean ret;
		int errorCode;

		lblMessage.setText(SysUtil.WORKING);
		invalidate();

		ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, false);

		if (!ret) {
			lblMessage.setText(SysUtil.NO_DEVICE);
			return;
		}

		ret = SBXPCProxy.ReadAllSLogData(SysUtil.MachineNumber);

		if (ret) {
			errorCode = 0;

			if (chkSearchAndDelete.isSelected())
				ret = SBXPCProxy.EmptySuperLogData(SysUtil.MachineNumber);

			lblMessage.setText("Getting...");
			invalidate();

			SuperLogDataOutput output;
			while (true) {
				output = SBXPCProxy.GetAllSLogData(SysUtil.MachineNumber);

				if (!output.isSuccess())
					break;

				superLogListModel.addSLogData(output);
			}
			lblTotal.setText("Total: " + superLogListModel.getRowCount());
		} else {
			errorCode = (int) SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;
		}

		lblMessage.setText(SysUtil.ErrorPrint(errorCode));

		ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
	}

	private void btnEmptySLogData_actionPerformed(ActionEvent evt) {
		superLogListModel.removeAll();
		tblLogList.setModel(superLogListModel);

		boolean ret;
		int errorCode;

		lblMessage.setText(SysUtil.WORKING);
		invalidate();

		ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, false);

		if (!ret) {
			lblMessage.setText(SysUtil.NO_DEVICE);
			return;
		}

		ret = SBXPCProxy.EmptySuperLogData(SysUtil.MachineNumber);

		if (ret)
			errorCode = 0;
		else
			errorCode = (int) SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;

		lblMessage.setText(SysUtil.ErrorPrint(errorCode));

		ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
	}

	private void btnEmptyGLogData_actionPerformed(ActionEvent evt) {
		superLogListModel.removeAll();
		tblLogList.setModel(superLogListModel);

		boolean ret;
		int errorCode;

		lblMessage.setText(SysUtil.WORKING);
		invalidate();

		ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, false);

		if (!ret) {
			lblMessage.setText(SysUtil.NO_DEVICE);
			return;
		}

		ret = SBXPCProxy.EmptyGeneralLogData(SysUtil.MachineNumber);

		if (ret)
			errorCode = 0;
		else
			errorCode = (int) SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;

		lblMessage.setText(SysUtil.ErrorPrint(errorCode));

		ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
	}

	private void btnReadGLogData_actionPerformed(ActionEvent evt) {
		generalLogListMOdel.removeAll();
		tblLogList.setModel(generalLogListMOdel);

		boolean ret;
		int errorCode;

		lblMessage.setText(SysUtil.WORKING);
		invalidate();

		ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, false);

		if (!ret) {
			lblMessage.setText(SysUtil.NO_DEVICE);
			return;
		}

		ret = SBXPCProxy.ReadGeneralLogData(SysUtil.MachineNumber, chkReadMark.isSelected());

		if (ret) {
			errorCode = 0;

			if (chkSearchAndDelete.isSelected())
				ret = SBXPCProxy.EmptyGeneralLogData(SysUtil.MachineNumber);

			lblMessage.setText("Getting...");
			invalidate();

			GeneralLogDataOutput output;
			while (true) {
				output = SBXPCProxy.GetGeneralLogData(SysUtil.MachineNumber);

				if (!output.isSuccess())
					break;

				generalLogListMOdel.addSLogData(output);
			}
			lblTotal.setText("Total: " + generalLogListMOdel.getRowCount());
		} else {
			errorCode = (int) SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;
		}

		lblMessage.setText(SysUtil.ErrorPrint(errorCode));

		ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
	}

	private void btnReadAllGLogData_actionPerformed(ActionEvent evt) {
		generalLogListMOdel.removeAll();
		tblLogList.setModel(generalLogListMOdel);

		boolean ret;
		int errorCode;

		lblMessage.setText(SysUtil.WORKING);
		invalidate();

		ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, false);

		if (!ret) {
			lblMessage.setText(SysUtil.NO_DEVICE);
			return;
		}

		ret = SBXPCProxy.ReadAllGLogData(SysUtil.MachineNumber);

		if (ret) {
			errorCode = 0;

			if (chkSearchAndDelete.isSelected())
				ret = SBXPCProxy.EmptyGeneralLogData(SysUtil.MachineNumber);

			lblMessage.setText("Getting...");
			invalidate();

			GeneralLogDataOutput output;
			while (true) {
				output = SBXPCProxy.GetAllGLogData(SysUtil.MachineNumber);

				if (!output.isSuccess())
					break;

				generalLogListMOdel.addSLogData(output);
			}
			lblTotal.setText("Total: " + generalLogListMOdel.getRowCount());
		} else {
			errorCode = (int) SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;
		}

		lblMessage.setText(SysUtil.ErrorPrint(errorCode));

		ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
	}

	private void tblLogListMouseClicked(java.awt.event.MouseEvent evt) {
		if (!chkShowGLogPhoto.isSelected())
			return;
		int selectedRow = tblLogList.getSelectedRow();
		if (!(tblLogList.getModel() instanceof GLogDataListModel))
			return;
		if (selectedRow == prevSelectedRow)
			return;
		prevSelectedRow = selectedRow;

		lblGLogPhoto.setIcon(null);

		if ("No Photo".equals(tblLogList.getValueAt(selectedRow, 0)))
			return;

		boolean ret;
		int errorCode;

		lblMessage.setText(SysUtil.WORKING);
		invalidate();

		ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, false);

		if (!ret) {
			lblMessage.setText(SysUtil.NO_DEVICE);
			return;
		}

		long photoPos = Long.parseLong(tblLogList.getValueAt(selectedRow, 0).toString());
		OneStringOutput output;
		output = SysUtil.MakeXMLCommandHeader("GetGLogPhotoData");
		output = SBXPCProxy.XML_AddLong(output.value, "PhotoPos", photoPos);

		output = SBXPCProxy.GeneralOperationXML(SysUtil.MachineNumber, output.value);

		if (output.isSuccess()) {
			errorCode = 0;
			XMLParseBinaryByteOutput parseOutput;
			parseOutput = SBXPCProxy.XML_ParseBinaryByte(output.value, "PhotoData", SysUtil.COMPRESSED_PHOTO_SIZE);
			if (parseOutput.isSuccess())
				lblGLogPhoto.setIcon(new ImageIcon(parseOutput.pData, "TEMP_GLOG_PHOTO"));
		} else {
			errorCode = (int) SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;
		}

		lblMessage.setText(SysUtil.ErrorPrint(errorCode));

		ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
	}

	private void btnDeleteGLogPhoto_actionPerformed(ActionEvent evt) {
		int selectedRow = tblLogList.getSelectedRow();
		if (selectedRow == -1) {
			lblMessage.setText("Please select log to delete photo.");
			return;
		}
		if ("No Photo".equals(tblLogList.getValueAt(selectedRow, 0))) {
			lblMessage.setText("No Photo Id");
			return;
		}
		long photoPos = Long.parseLong(tblLogList.getValueAt(selectedRow, 0).toString());
		OneStringOutput output;
		output = SysUtil.MakeXMLCommandHeader("DeleteGLogPhotoData");
		output = SBXPCProxy.XML_AddLong(output.value, "PhotoPos", photoPos);

		output = SBXPCProxy.GeneralOperationXML(SysUtil.MachineNumber, output.value);

		if (output.isSuccess()) {
			String strResultCode = SBXPCProxy.XML_ParseString(output.value, "ResultCode").value;
			if (strResultCode.equals("Success"))
				lblMessage.setText("Delete GLog Photo Success. (photoPos=" + String.valueOf(photoPos) + ")");
			else if (strResultCode.equals("No Photo"))
				lblMessage.setText("No Photo");
			else if (strResultCode.equals("InvalidParam"))
				lblMessage.setText("Invalid Parameter.");
			else
				lblMessage.setText("Unknown Error");
		} else {
			int errorCode = (int) SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;
			lblMessage.setText(SysUtil.ErrorPrint(errorCode));
		}
	}

	///////////////////////////////////
	class SLogDataListModel extends AbstractTableModel {
		final String[] COLUMN_TEXT = { "TMNo", "SEnlNo", "SMNo", "GEnlNo", "GMNo", "Manipulation", "FpNo",
				"DateTime", };
		List<SuperLogData> logList;

		public void addSLogData(SuperLogData logData) {
			logList.add(logData);
			fireTableRowsInserted(logList.size() - 1, logList.size() - 1);
		}

		public void removeAll() {
			logList.removeAll(logList);
			fireTableDataChanged();
		}

		public SLogDataListModel() {
			logList = new ArrayList<SuperLogData>();
		}

		public int getRowCount() {
			return logList.size();
		}

		public int getColumnCount() {
			return COLUMN_TEXT.length;
		}

		public Object getValueAt(int rowIndex, int columnIndex) {
			SuperLogData logData = logList.get(rowIndex);
			switch (columnIndex) {
			case 0:
				return logData.dwTMachineNumber;
			case 1:
				return logData.dwSEnrollNumber;
			case 2:
				return logData.dwSMachineNumber;
			case 3:
				return logData.dwGEnrollNumber;
			case 4:
				return logData.dwGMachineNumber;
			case 5: {
				String ret;
				switch ((int) logData.dwManipulation) {
				case 3:
					ret = String.valueOf(logData.dwManipulation) + "--" + "Enroll User";
					break;
				case 4:
					ret = String.valueOf(logData.dwManipulation) + "--" + "Enroll Manager";
					break;
				case 5:
					ret = String.valueOf(logData.dwManipulation) + "--" + "Delete Fp Data";
					break;
				case 6:
					ret = String.valueOf(logData.dwManipulation) + "--" + "Delete Password";
					break;
				case 7:
					ret = String.valueOf(logData.dwManipulation) + "--" + "Delete Card Data";
					break;
				case 8:
					ret = String.valueOf(logData.dwManipulation) + "--" + "Delete All LogData";
					break;
				case 9:
					ret = String.valueOf(logData.dwManipulation) + "--" + "Modify System Info";
					break;
				case 10:
					ret = String.valueOf(logData.dwManipulation) + "--" + "Modify System Time";
					break;
				case 11:
					ret = String.valueOf(logData.dwManipulation) + "--" + "Modify Log Setting";
					break;
				case 12:
					ret = String.valueOf(logData.dwManipulation) + "--" + "Modify Comm Setting";
					break;
				case 13:
					ret = String.valueOf(logData.dwManipulation) + "--" + "Modify Timezone Setting";
					break;
				case 14:
					ret = String.valueOf(logData.dwManipulation) + "--" + "Delete Face";
					break;
				default:
					ret = "--Unknown--";
				}
				return ret;
			}
			case 6:
				if (logData.dwBackupNumber < 10)
					return logData.dwBackupNumber;
				else if (logData.dwBackupNumber == 10)
					return "Password";
				else if (logData.dwBackupNumber == 14)
					return "FACE";
				else
					return "Card";
			case 7: {
				NumberFormat formatter = new DecimalFormat("00");
				String ret = String.valueOf(logData.dwYear) + "/" + formatter.format(logData.dwMonth) + "/"
						+ formatter.format(logData.dwDay) + " ";
				ret += formatter.format(logData.dwHour) + ":" + formatter.format(logData.dwMinute) + ":"
						+ formatter.format(logData.dwSecond);
				return ret;
			}
			default:
				return null;
			}
		}

		@Override
		public String getColumnName(int columnIndex) {
			return COLUMN_TEXT[columnIndex];
		}
	}

	class GLogDataListModel extends AbstractTableModel {
		final String[] COLUMN_TEXT = { "PhotoNo", "EnrollNo", "EMachineNo", "VeriMode", "DateTime", "DaiGong", };
		List<GeneralLogData> logList;

		public void addSLogData(GeneralLogData logData) {
			logList.add(logData);
			fireTableRowsInserted(logList.size() - 1, logList.size() - 1);
		}

		public void removeAll() {
			logList.removeAll(logList);
			fireTableDataChanged();
		}

		public GLogDataListModel() {
			logList = new ArrayList<GeneralLogData>();
		}

		public int getRowCount() {
			return logList.size();
		}

		public int getColumnCount() {
			return COLUMN_TEXT.length;
		}

		public Object getValueAt(int rowIndex, int columnIndex) {
			GeneralLogData logData = logList.get(rowIndex);

			int attendStatus, antipassStatus, daigong, verifyMode;

			antipassStatus = (int) logData.dwVerifyMode / 65536;
			daigong = antipassStatus / 4;
			antipassStatus = antipassStatus % 4;
			verifyMode = (int) logData.dwVerifyMode % 65536;
			attendStatus = verifyMode / 256;
			verifyMode = verifyMode % 256;

			String strAttendStatus, strAntipassStatus, strVerifyMode;
			switch (attendStatus) {
			case 0:
				strAttendStatus = "_Duty On";
				break;
			case 1:
				strAttendStatus = "_Duty Off";
				break;
			case 2:
				strAttendStatus = "_Overtime On";
				break;
			case 3:
				strAttendStatus = "_Overtime Off";
				break;
			case 4:
				strAttendStatus = "_Go In";
				break;
			case 5:
				strAttendStatus = "_Go Out";
				break;
			default:
				strAttendStatus = "";
			}

			switch (antipassStatus) {
			case 1:
				strAntipassStatus = ":AP_In";
				break;
			case 2:
				strAntipassStatus = ":AP_Out";
				break;
			default:
				strAntipassStatus = "";
			}

			switch (verifyMode) {
			case 0:
				strVerifyMode = "FP+ID";
				break;
			case 1:
				strVerifyMode = "FP";
				break;
			case 2:
				strVerifyMode = "Password";
				break;
			case 3:
				strVerifyMode = "Card";
				break;
			case 4:
				strVerifyMode = "FP+Card";
				break;
			case 5:
				strVerifyMode = "FP+Pwd";
				break;
			case 6:
				strVerifyMode = "Card+Pwd";
				break;
			case 7:
				strVerifyMode = "FP+Card+Pwd";
				break;
			case 10:
				strVerifyMode = "Hand Lock";
				break;
			case 11:
				strVerifyMode = "Prog Lock";
				break;
			case 12:
				strVerifyMode = "Prog Open";
				break;
			case 13:
				strVerifyMode = "Prog Close";
				break;
			case 14:
				strVerifyMode = "Auto Recover";
				break;
			case 20:
				strVerifyMode = "Lock Over";
				break;
			case 21:
				strVerifyMode = "Illegal Open";
				break;
			case 22:
				strVerifyMode = "Duress alarm";
				break;
			case 23:
				strVerifyMode = "Tamper detect";
				break;
            case 30: strVerifyMode = "FACE"; break;
            case 31: strVerifyMode = "FACE+CARD"; break;
            case 32: strVerifyMode = "FACE+PWD"; break;
            case 33: strVerifyMode = "FACE+CARD+PWD"; break;
            case 34: strVerifyMode = "FACE+FP"; break;
			case 51:
				strVerifyMode = "FP";
				break;
			case 52:
				strVerifyMode = "Password";
				break;
			case 53:
				strVerifyMode = "Card";
				break;
			case 101:
				strVerifyMode = "FP";
				break;
			case 102:
				strVerifyMode = "Password";
				break;
			case 103:
				strVerifyMode = "Card";
				break;
			case 151:
				strVerifyMode = "FP";
				break;
			case 152:
				strVerifyMode = "Password";
				break;
			case 153:
				strVerifyMode = "Card";
				break;
			default:
				strVerifyMode = "";
				break;
			}

			switch (columnIndex) {
			case 0:
				return (logData.dwTMachineNumber == -1 ? "No Photo" : logData.dwTMachineNumber);
			case 1:
				return logData.dwEnrollNumber;
			case 2:
				return logData.dwEMachineNumber;
			case 3:
				return strVerifyMode + strAttendStatus + strAntipassStatus;
			case 4: 
				NumberFormat formatter = new DecimalFormat("00");
				String ret = String.valueOf(logData.dwYear) + "/" + formatter.format(logData.dwMonth) + "/"
						+ formatter.format(logData.dwDay) + " ";
				ret += formatter.format(logData.dwHour) + ":" + formatter.format(logData.dwMinute) + ":"
						+ formatter.format(logData.dwSecond);
				return ret;
			case 5:
				return String.valueOf(daigong);
			default:
				return null;
			}
		}

		@Override
		public String getColumnName(int columnIndex) {
			return COLUMN_TEXT[columnIndex];
		}
	}
}
