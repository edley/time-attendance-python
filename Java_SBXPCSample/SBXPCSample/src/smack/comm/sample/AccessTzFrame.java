package smack.comm.sample;

import java.awt.EventQueue;
import java.awt.Font;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.text.DecimalFormat;
import java.text.NumberFormat;
import java.util.Calendar;
import java.util.Date;

import javax.swing.AbstractListModel;
import javax.swing.JButton;
import javax.swing.JComboBox;
import javax.swing.JFormattedTextField;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JList;
import javax.swing.JScrollPane;
import javax.swing.SwingConstants;

import smack.comm.SBXPCProxy;
import smack.comm.output.GetDeviceLongInfoOutput;
import smack.comm.sample.global.SysUtil;

public class AccessTzFrame extends JFrame {
	private JLabel lblMessage;
	private JLabel lblStart;
	private JLabel lblEnd;
	private JFormattedTextField txtStart;
	private JFormattedTextField txtEnd;
	private JLabel lblVerifyMode;
	private JComboBox cmbVerifyMode;
	private JScrollPane scrollPane;
	private JList lstTimezoneList;
	private JButton btnUpdate;
	private JButton btnRead;
	private JButton btnWrite;

    
    TimeZoneListModel listModel = new TimeZoneListModel();

	/**
	 * Launch the application.
	 */
	public static void main(String[] args) {
		EventQueue.invokeLater(new Runnable() {
			public void run() {
				try {
					AccessTzFrame frame = new AccessTzFrame();
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
	public AccessTzFrame() {
		addWindowListener(new WindowAdapter() {
			@Override
			public void windowClosing(WindowEvent arg0) {
				if (MainFrame.getInstance() != null)
					MainFrame.getInstance().setVisible(true);
			}
		});
		
		setTitle("Access TimeZone");
		setBounds(100, 100, 533, 542);
		setDefaultCloseOperation(javax.swing.WindowConstants.DISPOSE_ON_CLOSE);
		getContentPane().setLayout(null);
		
		lblMessage = new JLabel("Message");
		lblMessage.setHorizontalAlignment(SwingConstants.CENTER);
		lblMessage.setFont(new Font("Segoe UI", Font.BOLD, 18));
		lblMessage.setBorder(javax.swing.BorderFactory.createBevelBorder(javax.swing.border.BevelBorder.LOWERED));
		lblMessage.setBounds(10, 11, 497, 36);
		getContentPane().add(lblMessage);
		
		lblStart = new JLabel("Start:");
		lblStart.setBounds(10, 58, 46, 14);
		getContentPane().add(lblStart);
		
		lblEnd = new JLabel("End:");
		lblEnd.setBounds(10, 83, 46, 14);
		getContentPane().add(lblEnd);
		
		txtStart = new JFormattedTextField();
		txtStart.setBounds(66, 55, 107, 20);
        txtStart.setFormatterFactory(new javax.swing.text.DefaultFormatterFactory(new javax.swing.text.DateFormatter(java.text.DateFormat.getTimeInstance(java.text.DateFormat.SHORT))));
        getContentPane().add(txtStart);
		
		txtEnd = new JFormattedTextField();
		txtEnd.setBounds(66, 80, 107, 20);
		txtEnd.setFormatterFactory(new javax.swing.text.DefaultFormatterFactory(new javax.swing.text.DateFormatter(java.text.DateFormat.getTimeInstance(java.text.DateFormat.SHORT))));
        getContentPane().add(txtEnd);
		
		lblVerifyMode = new JLabel("Verify Mode");
		lblVerifyMode.setBounds(228, 58, 107, 14);
		getContentPane().add(lblVerifyMode);
		
		cmbVerifyMode = new JComboBox();
		cmbVerifyMode.setBounds(238, 80, 165, 20);
        cmbVerifyMode.setModel(new javax.swing.DefaultComboBoxModel(new String[] { "FP|CD|PWD", "CD&FP", "FP&PWD", "CD&PWD", "FP&CD&PWD", "System Default VM", "FP", "CD", "ID&FP", "ID&PWD" }));
        getContentPane().add(cmbVerifyMode);
		
		scrollPane = new JScrollPane();
		scrollPane.setBounds(10, 116, 393, 375);
		getContentPane().add(scrollPane);
		
		lstTimezoneList = new JList();
		lstTimezoneList.addMouseListener(new MouseAdapter() {
			@Override
			public void mouseClicked(MouseEvent arg0) {
				lstTimezoneListMouseClicked(arg0);
			}
		});
		lstTimezoneList.setModel(listModel);
		scrollPane.setViewportView(lstTimezoneList);
		
		btnUpdate = new JButton("Update");
		btnUpdate.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnUpdateActionPerformed(arg0);
			}
		});
		btnUpdate.setBounds(413, 116, 89, 32);
		getContentPane().add(btnUpdate);
		
		btnRead = new JButton("Read");
		btnRead.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnReadActionPerformed(arg0);
			}
		});
		btnRead.setBounds(413, 252, 89, 32);
		getContentPane().add(btnRead);
		
		btnWrite = new JButton("Write");
		btnWrite.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnWriteActionPerformed(arg0);
			}
		});
		btnWrite.setBounds(413, 322, 89, 32);
		getContentPane().add(btnWrite);

	}
	
	private void lstTimezoneListMouseClicked(java.awt.event.MouseEvent evt) {

        DbTimeSection timeSection = (DbTimeSection)lstTimezoneList.getSelectedValue();
        
        if(timeSection == null)
            return;
        
        Calendar calendar = Calendar.getInstance();
        calendar.set(Calendar.HOUR_OF_DAY, (int)timeSection.startHour);
        calendar.set(Calendar.MINUTE, (int)timeSection.startMinute);
        txtStart.setValue(calendar.getTime());
        
        calendar.set(Calendar.HOUR_OF_DAY, (int)timeSection.endHour);
        calendar.set(Calendar.MINUTE, (int)timeSection.endMinute);
        txtEnd.setValue(calendar.getTime());
        
        cmbVerifyMode.setSelectedIndex((int)timeSection.verifyMode);
    }

    private void btnReadActionPerformed(java.awt.event.ActionEvent evt) {
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
        
        GetDeviceLongInfoOutput output;
        output = SBXPCProxy.GetDeviceLongInfo(SysUtil.MachineNumber, 3);
        
        if(output.isSuccess())
        {
            listModel.setAllData(output);
            errorCode = 0;
        }else
        {
            errorCode = (int)SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;
        }
        
        lblMessage.setText(SysUtil.ErrorPrint(errorCode));
        
        ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
    }

    private void btnWriteActionPerformed(java.awt.event.ActionEvent evt) {
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
        
        ret = SBXPCProxy.SetDeviceLongInfo(SysUtil.MachineNumber, 3, listModel.getAllData());
        if(ret)
            errorCode = 0;
        else
            errorCode = (int)SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;
        
        lblMessage.setText(SysUtil.ErrorPrint(errorCode));
        
        ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
    }

    private void btnUpdateActionPerformed(java.awt.event.ActionEvent evt) {
        int index = lstTimezoneList.getSelectedIndex();
        if(index == -1)
            return;

        int timeZoneIndex = index / TimeZoneListModel.TIME_SECTION_COUNT;
        int timeSectionIndex  = index % TimeZoneListModel.TIME_SECTION_COUNT;
        DbTimeSection timeSection = new DbTimeSection(timeZoneIndex, timeSectionIndex);
        
        Calendar calendar = Calendar.getInstance();
        
        calendar.setTime((Date)txtStart.getValue());
        timeSection.startHour = calendar.get(Calendar.HOUR_OF_DAY);
        timeSection.startMinute = calendar.get(Calendar.MINUTE);
        
        calendar.setTime((Date)txtEnd.getValue());
        timeSection. endHour = calendar.get(Calendar.HOUR_OF_DAY);
        timeSection.endMinute = calendar.get(Calendar.MINUTE);
        
        timeSection.verifyMode = cmbVerifyMode.getSelectedIndex();
        
        listModel.setItemData(lstTimezoneList.getSelectedIndex(), timeSection);
    }


    public class DbTimeSection
    {
        public static final byte DEFAULT_VM = 5;
        
        private final int timeZoneIndex;
        private final int timeSectionIndex;
        
        public int startHour;
        public int startMinute;
        public int endHour;
        public int endMinute;
        public int verifyMode;
        
        public DbTimeSection(int zoneIndex, int sectionIndex)
        {
            timeZoneIndex = zoneIndex;
            timeSectionIndex = sectionIndex;
            
            startHour = 0;
            startMinute = 0;
            endHour = 23;
            endMinute = 59;
            verifyMode = DEFAULT_VM;
        }
        
        @Override
        public String toString()
        {
            String ret = "";
            NumberFormat formatter = new DecimalFormat("000");
            NumberFormat time_formatter = new DecimalFormat("00");
            ret += "[Tz] " + formatter.format(timeZoneIndex) + "-" + formatter.format(timeSectionIndex);
            ret += "[S] " + time_formatter.format(startHour) + ":" + time_formatter.format(startMinute) + " ";
            ret += "[E] " + time_formatter.format(endHour) + ":" + time_formatter.format(endMinute) + " ";
            if(verifyMode < 0) verifyMode = 0;
            if(verifyMode >= cmbVerifyMode.getItemCount()) verifyMode = cmbVerifyMode.getItemCount() - 1;
            ret += "[VM] " + cmbVerifyMode.getItemAt((int)verifyMode);
            return ret;
        }
    }
    
    class TimeZoneListModel extends AbstractListModel
    {
        public static final int TIME_ZONE_COUNT = 50;
        public static final int TIME_SECTION_COUNT = 8;
        public static final int ELEM_CNT = 5;
        public static final int TIME_ZONE_LIST_SIZE = TIME_ZONE_COUNT * TIME_SECTION_COUNT;
        public static final int VM_TZONE_COUNT = 10;

        private DbTimeSection[] timezoneInfoList;

        public TimeZoneListModel()
        {
            timezoneInfoList = new DbTimeSection[TIME_ZONE_LIST_SIZE];
            for(int i = 0; i < TIME_ZONE_COUNT; i ++)
            {
                for(int j = 0; j < TIME_SECTION_COUNT; j ++)
                    timezoneInfoList[i * TIME_SECTION_COUNT + j] = new DbTimeSection(i, j);
            }
        }
        
        public void setAllData(GetDeviceLongInfoOutput data)
        {
            int index; 
            if(data.value.length < TIME_ZONE_LIST_SIZE * ELEM_CNT)
                return;
            for(int i = 0; i < TIME_ZONE_COUNT; i ++)
            {
                for(int j = 0; j < TIME_SECTION_COUNT; j ++)
                {
                    index = i * TIME_SECTION_COUNT + j;
                    timezoneInfoList[index].startHour   = data.value[index * ELEM_CNT + 0];
                    timezoneInfoList[index].startMinute = data.value[index * ELEM_CNT + 1];
                    timezoneInfoList[index].endHour     = data.value[index * ELEM_CNT + 2];
                    timezoneInfoList[index].endMinute   = data.value[index * ELEM_CNT + 3];
                    timezoneInfoList[index].verifyMode  = data.value[index * ELEM_CNT + 4];
                    checkData(index, timezoneInfoList[index]);
                }
            }
            fireContentsChanged(this, 0, getSize());
        }
        
        public int[] getAllData()
        {
            int[] ret = new int[TIME_ZONE_LIST_SIZE * ELEM_CNT];
            int index;
            for(int i = 0; i < TIME_ZONE_COUNT; i ++)
            {
                for(int j = 0; j < TIME_SECTION_COUNT; j ++)
                {
                    index = i * TIME_SECTION_COUNT + j;
                    ret[index * ELEM_CNT + 0] = timezoneInfoList[index].startHour;
                    ret[index * ELEM_CNT + 1] = timezoneInfoList[index].startMinute;
                    ret[index * ELEM_CNT + 2] = timezoneInfoList[index].endHour;
                    ret[index * ELEM_CNT + 3] = timezoneInfoList[index].endMinute;
                    ret[index * ELEM_CNT + 4] = timezoneInfoList[index].verifyMode;
                }
            }
            return ret;
        }
        
        public void setItemData(int index, DbTimeSection timeSection)
        {
            if(index < 0 || index > TIME_ZONE_LIST_SIZE)
                return;
            
            checkData(index, timeSection);            
            timezoneInfoList[index] = timeSection;
            
            fireContentsChanged(this, index, index);
        }
        
        private boolean checkData(int index, DbTimeSection timeSection)
        {
            boolean ret = true;
            
            if(index >= VM_TZONE_COUNT * TIME_SECTION_COUNT)
                timeSection.verifyMode  = DbTimeSection.DEFAULT_VM;
            
            if(timeSection.verifyMode < 0 ) 
            {
                timeSection.verifyMode = 0;
                ret = false;
            }
            if(timeSection.verifyMode > cmbVerifyMode.getItemCount()) 
            {
                timeSection.verifyMode = cmbVerifyMode.getItemCount() - 1;
                ret = false;
            }
            
            return ret;
        }


        public int getSize() {
            return TIME_ZONE_LIST_SIZE;
        }

        public Object getElementAt(int index) {
            return timezoneInfoList[index];
        }

    }
}
