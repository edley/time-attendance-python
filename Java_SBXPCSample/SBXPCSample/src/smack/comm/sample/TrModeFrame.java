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
import javax.swing.JTextField;
import javax.swing.SwingConstants;

import smack.comm.SBXPCProxy;
import smack.comm.output.GetDeviceLongInfoOutput;
import smack.comm.sample.global.SysUtil;

public class TrModeFrame extends JFrame {
	private JLabel lblMessage;
	private JLabel lblStart;
	private JLabel lblEnd;
	private JFormattedTextField txtStart;
	private JFormattedTextField txtEnd;
	private JLabel lblNewLabel;
	private JComboBox cmbTrStatus;
	private JList lstTrModeList;
	private JScrollPane scrollPane;
	private JButton btnUpdate;
	private JButton btnRead;
	private JButton btnWrite;

	   
    TrModeListModel listModel = new TrModeListModel();

	/**
	 * Launch the application.
	 */
	public static void main(String[] args) {
		EventQueue.invokeLater(new Runnable() {
			public void run() {
				try {
					TrModeFrame frame = new TrModeFrame();
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
	public TrModeFrame() {
		addWindowListener(new WindowAdapter() {
			@Override
			public void windowClosing(WindowEvent arg0) {
				if (MainFrame.getInstance() != null)
					MainFrame.getInstance().setVisible(true);
			}
		});

		setTitle("TimeMode Zone");
		setBounds(100, 100, 453, 480);
		setDefaultCloseOperation(javax.swing.WindowConstants.DISPOSE_ON_CLOSE);
		getContentPane().setLayout(null);
		
		lblMessage = new JLabel("Message");
		lblMessage.setHorizontalAlignment(SwingConstants.CENTER);
		lblMessage.setFont(new Font("Segoe UI", Font.BOLD, 18));
		lblMessage.setBorder(javax.swing.BorderFactory.createBevelBorder(javax.swing.border.BevelBorder.LOWERED));
		lblMessage.setBounds(10, 11, 416, 36);
		getContentPane().add(lblMessage);
		
		lblStart = new JLabel("Start:");
		lblStart.setBounds(10, 61, 46, 14);
		getContentPane().add(lblStart);
		
		lblEnd = new JLabel("End:");
		lblEnd.setBounds(10, 89, 46, 14);
		getContentPane().add(lblEnd);
		
		txtStart = new JFormattedTextField();
		txtStart.setBounds(69, 58, 86, 20);
		getContentPane().add(txtStart);
		txtStart.setColumns(10);
        txtStart.setFormatterFactory(new javax.swing.text.DefaultFormatterFactory(new javax.swing.text.DateFormatter(java.text.DateFormat.getTimeInstance(java.text.DateFormat.SHORT))));

		txtEnd = new JFormattedTextField();
		txtEnd.setBounds(69, 86, 86, 20);
		getContentPane().add(txtEnd);
		txtEnd.setColumns(10);
		txtEnd.setFormatterFactory(new javax.swing.text.DefaultFormatterFactory(new javax.swing.text.DateFormatter(java.text.DateFormat.getTimeInstance(java.text.DateFormat.SHORT))));

		lblNewLabel = new JLabel("In/Out Status:");
		lblNewLabel.setBounds(218, 61, 104, 14);
		getContentPane().add(lblNewLabel);
		
		cmbTrStatus = new JComboBox();
		cmbTrStatus.setBounds(218, 86, 104, 20);
        cmbTrStatus.setModel(new javax.swing.DefaultComboBoxModel(new String[] { "Duty On", "Duty Off", "OverTime On", "OverTime Off", "Return", "Go Out" }));
		getContentPane().add(cmbTrStatus);

		scrollPane = new JScrollPane();
		scrollPane.setBounds(10, 133, 312, 297);
		getContentPane().add(scrollPane);
		
		lstTrModeList = new JList();
		lstTrModeList.addMouseListener(new MouseAdapter() {
			@Override
			public void mouseClicked(MouseEvent arg0) {
				lstTrModeListMouseClicked(arg0);
			}
		});
		lstTrModeList.setModel(listModel);
		scrollPane.setViewportView(lstTrModeList);
		
		btnUpdate = new JButton("Update");
		btnUpdate.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnUpdateMouseClicked(arg0);
			}
		});
		btnUpdate.setBounds(332, 133, 89, 30);
		getContentPane().add(btnUpdate);
		
		btnRead = new JButton("Read");
		btnRead.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnReadMouseClicked(arg0);
			}
		});
		btnRead.setBounds(332, 271, 89, 30);
		getContentPane().add(btnRead);
		
		btnWrite = new JButton("Write");
		btnWrite.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnWriteMouseClicked(arg0);
			}
		});
		btnWrite.setBounds(332, 326, 89, 30);
		getContentPane().add(btnWrite);

	}

	
    public class DbTrMode
    {
        public final int index;
        
        public int startHour;
        public int startMinute;
        public int endHour;
        public int endMinute;
        public int trStatus;
        
        public DbTrMode(int index)
        {
            this.index = index;
            startHour = 0;
            startMinute = 0;
            endHour = 0;
            endMinute = 0;
            trStatus = 0;
        }
        
        @Override
        public String toString()
        {
            NumberFormat formatter = new DecimalFormat("00");
            String ret;
            ret = "[No.] " + index + " ";
            ret += "[S] " + formatter.format(startHour) + ":" + formatter.format(startMinute) + " ";
            ret += "[E] " + formatter.format(endHour) + ":" + formatter.format(endMinute) + " ";
            ret += "[Status] " + cmbTrStatus.getItemAt(trStatus);
            
            return ret;
        }
    }
    
    public class TrModeListModel extends AbstractListModel
    {
        public static final int TRMODE_COUNT = 10;
        public static final int ELEM_CNT = 5;
        
        DbTrMode[] trModeList = new DbTrMode[TRMODE_COUNT];
        
        public TrModeListModel()
        {
            for(int i = 0; i< TRMODE_COUNT; i ++)
                trModeList[i] = new DbTrMode(i);
        }
        
        public void setAllData(GetDeviceLongInfoOutput data)
        {
            if(data.value.length < TRMODE_COUNT * ELEM_CNT)
                return;
            
            for(int i = 0; i < TRMODE_COUNT; i ++)
            {
                trModeList[i].trStatus      = data.value[i * ELEM_CNT + 0];
                trModeList[i].startHour     = data.value[i * ELEM_CNT + 1];
                trModeList[i].startMinute   = data.value[i * ELEM_CNT + 2];
                trModeList[i].endHour       = data.value[i * ELEM_CNT + 3];
                trModeList[i].endMinute     = data.value[i * ELEM_CNT + 4];
            }
            fireContentsChanged(this, 0, getSize());
        }
        
        public int[] getAllData()
        {
            int[] ret = new int[TRMODE_COUNT * ELEM_CNT];
            
            int index;
            
            for(int i = 0; i < TRMODE_COUNT; i ++)
            {
                index = i * ELEM_CNT;
                ret[index + 0] = trModeList[i].trStatus;
                ret[index + 1] = trModeList[i].startHour;
                ret[index + 2] = trModeList[i].startMinute;
                ret[index + 3] = trModeList[i].endHour;
                ret[index + 4] = trModeList[i].endMinute;
            }
            
            return ret;
        }
        
        public void setElementAt(int index, DbTrMode trMode)
        {
            if(index < 0 || index >= TRMODE_COUNT)
                return;

            trModeList[index] = trMode;
            
            fireContentsChanged(this, index, index);
        }
        
        private boolean checkData(DbTrMode trMode)
        {
            if(trMode.trStatus < 0)
            {
                trMode.trStatus = 0;
                return false;
            }
            if(trMode.trStatus >= cmbTrStatus.getItemCount())
            {
                trMode.trStatus = cmbTrStatus.getItemCount() - 1;
                return false;
            }
            
            return true;
        }
        
        public int getSize() {
            return TRMODE_COUNT;
        }

        public Object getElementAt(int index) {
            return trModeList[index];
        }        
    }

    
    private void lstTrModeListMouseClicked(java.awt.event.MouseEvent evt) {
        
        DbTrMode trMode = (DbTrMode)lstTrModeList.getSelectedValue();
        if(trMode == null)
            return;
        
        Calendar calendar = Calendar.getInstance();
        calendar.set(Calendar.HOUR_OF_DAY, trMode.startHour);
        calendar.set(Calendar.MINUTE, trMode.startMinute);
        txtStart.setValue(calendar.getTime());
        
        calendar.set(Calendar.HOUR_OF_DAY, trMode.endHour);
        calendar.set(Calendar.MINUTE, trMode.endMinute);
        txtEnd.setValue(calendar.getTime());
        
        cmbTrStatus.setSelectedIndex(trMode.trStatus);
    }

    private void btnUpdateMouseClicked(ActionEvent evt) {
        
        int index = lstTrModeList.getSelectedIndex();
        if(index == -1)
            return;
        
        DbTrMode trMode = new DbTrMode(index);
        
        Calendar calendar = Calendar.getInstance();
        calendar.setTime((Date)txtStart.getValue());
        trMode.startHour = calendar.get(Calendar.HOUR_OF_DAY);
        trMode.startMinute = calendar.get(Calendar.MINUTE);
        
        calendar.setTime((Date)txtEnd.getValue());
        trMode.endHour = calendar.get(Calendar.HOUR_OF_DAY);
        trMode.endMinute = calendar.get(Calendar.MINUTE);
        
        trMode.trStatus = cmbTrStatus.getSelectedIndex();
        
        listModel.setElementAt(index, trMode);
    }

    private void btnReadMouseClicked(ActionEvent evt) {
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
        output = SBXPCProxy.GetDeviceLongInfo(SysUtil.MachineNumber, 5);
        
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

    private void btnWriteMouseClicked(ActionEvent evt) {
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
        
        ret = SBXPCProxy.SetDeviceLongInfo(SysUtil.MachineNumber, 5, listModel.getAllData());
        
        if(ret)
            errorCode = 0;
        else
            errorCode = (int)SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;
        
        lblMessage.setText(SysUtil.ErrorPrint(errorCode));
        
        ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
    }

}
