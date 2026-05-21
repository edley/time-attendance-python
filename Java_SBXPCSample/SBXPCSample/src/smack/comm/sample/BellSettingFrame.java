package smack.comm.sample;

import java.awt.EventQueue;
import java.awt.Font;
import java.awt.Rectangle;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;

import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JCheckBox;
import javax.swing.JTextField;
import javax.swing.SwingConstants;

import smack.comm.SBXPCProxy;
import smack.comm.output.GetBellTimeOutput;
import smack.comm.sample.global.SysUtil;

import javax.swing.JButton;
import java.awt.event.ActionListener;
import java.awt.event.ActionEvent;


public class BellSettingFrame extends JFrame {
	private JLabel lblMessage;
	private JLabel lblBellPoint;
	private JLabel lblUseFlag;
	private JLabel lblStartTime;
	private JLabel lblBellCount;
	private JLabel lblPoint_1;
	private JCheckBox chkUseFlag_1;
	private JTextField txtHour_1;
	private JTextField txtMinute_1;
	private JLabel lblColon_1;
	private JTextField txtBellCount;
	private JButton btnRead;
	private JButton btnWrite;
	private JTextField txtMinute_13;
	private JLabel lblColon_13;
	private JTextField txtHour_13;
	private JCheckBox chkUseFlag_13;
	private JLabel lblPoint_13;
	private JLabel label_2;
	private JLabel label_3;
	private JLabel label_4;

    JLabel[] 		lblPoints;
    JCheckBox[] 	chkUseFlags;
    JTextField[] 	txtHours;
    JLabel[] 		lblColons;
    JTextField[] 	txtMinutes;

    GetBellTimeOutput dbBellSetting;

    public static final int MAX_BELLCOUNT_DAY = 24;

	/**
	 * Launch the application.
	 */
	public static void main(String[] args) {
		EventQueue.invokeLater(new Runnable() {
			public void run() {
				try {
					BellSettingFrame frame = new BellSettingFrame();
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
	public BellSettingFrame() {
		addWindowListener(new WindowAdapter() {
			@Override
			public void windowClosing(WindowEvent arg0) {
				if (MainFrame.getInstance() != null)
					MainFrame.getInstance().setVisible(true);
			}
		});

		setTitle("Bell");
		setBounds(100, 100, 595, 533);
		setDefaultCloseOperation(javax.swing.WindowConstants.DISPOSE_ON_CLOSE);
		getContentPane().setLayout(null);
		
		lblMessage = new JLabel("Message");
		lblMessage.setHorizontalAlignment(SwingConstants.CENTER);
		lblMessage.setFont(new Font("Segoe UI", Font.BOLD, 18));
		lblMessage.setBorder(javax.swing.BorderFactory.createBevelBorder(javax.swing.border.BevelBorder.LOWERED));
		lblMessage.setBounds(10, 11, 559, 35);
		getContentPane().add(lblMessage);
		
		lblBellPoint = new JLabel("Bell Point");
		lblBellPoint.setBounds(20, 56, 61, 14);
		getContentPane().add(lblBellPoint);
		
		lblUseFlag = new JLabel("Use Flag");
		lblUseFlag.setBounds(86, 56, 61, 14);
		getContentPane().add(lblUseFlag);
		
		lblStartTime = new JLabel("Start Time");
		lblStartTime.setHorizontalAlignment(SwingConstants.CENTER);
		lblStartTime.setBounds(142, 56, 85, 14);
		getContentPane().add(lblStartTime);
		
		lblBellCount = new JLabel("Bell Count");
		lblBellCount.setHorizontalAlignment(SwingConstants.CENTER);
		lblBellCount.setBounds(249, 56, 71, 14);
		getContentPane().add(lblBellCount);
		
		lblPoint_1 = new JLabel("Point");
		lblPoint_1.setBounds(21, 81, 55, 14);
		getContentPane().add(lblPoint_1);
		
		chkUseFlag_1 = new JCheckBox("");
		chkUseFlag_1.setBounds(96, 77, 21, 23);
		getContentPane().add(chkUseFlag_1);
		
		txtHour_1 = new JTextField();
		txtHour_1.setBounds(141, 81, 33, 20);
		getContentPane().add(txtHour_1);
		txtHour_1.setColumns(10);
		
		txtMinute_1 = new JTextField();
		txtMinute_1.setBounds(194, 81, 33, 20);
		getContentPane().add(txtMinute_1);
		txtMinute_1.setColumns(10);
		
		lblColon_1 = new JLabel(":");
		lblColon_1.setHorizontalAlignment(SwingConstants.CENTER);
		lblColon_1.setBounds(180, 84, 11, 14);
		getContentPane().add(lblColon_1);
		
		txtBellCount = new JTextField();
		txtBellCount.setColumns(10);
		txtBellCount.setBounds(261, 81, 46, 20);
		getContentPane().add(txtBellCount);
		
		btnRead = new JButton("Read");
		btnRead.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnRead_actionPerformed(arg0);
			}
		});
		btnRead.setBounds(170, 447, 89, 23);
		getContentPane().add(btnRead);
		
		btnWrite = new JButton("Write");
		btnWrite.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnWrite_actionPerformed(arg0);
			}
		});
		btnWrite.setBounds(281, 447, 89, 23);
		getContentPane().add(btnWrite);
		
		txtMinute_13 = new JTextField();
		txtMinute_13.setColumns(10);
		txtMinute_13.setBounds(519, 81, 33, 20);
		getContentPane().add(txtMinute_13);
		
		lblColon_13 = new JLabel(":");
		lblColon_13.setHorizontalAlignment(SwingConstants.CENTER);
		lblColon_13.setBounds(505, 84, 11, 14);
		getContentPane().add(lblColon_13);
		
		txtHour_13 = new JTextField();
		txtHour_13.setColumns(10);
		txtHour_13.setBounds(466, 81, 33, 20);
		getContentPane().add(txtHour_13);
		
		chkUseFlag_13 = new JCheckBox("");
		chkUseFlag_13.setBounds(421, 77, 21, 23);
		getContentPane().add(chkUseFlag_13);
		
		lblPoint_13 = new JLabel("Point");
		lblPoint_13.setBounds(340, 81, 61, 14);
		getContentPane().add(lblPoint_13);
		
		label_2 = new JLabel("Start Time");
		label_2.setHorizontalAlignment(SwingConstants.CENTER);
		label_2.setBounds(467, 56, 85, 14);
		getContentPane().add(label_2);
		
		label_3 = new JLabel("Use Flag");
		label_3.setBounds(411, 56, 61, 14);
		getContentPane().add(label_3);
		
		label_4 = new JLabel("Bell Point");
		label_4.setBounds(340, 56, 61, 14);
		getContentPane().add(label_4);

		
		////////////////////////////////////////////////////////////////
        lblPoints = new JLabel[MAX_BELLCOUNT_DAY];
        chkUseFlags = new JCheckBox[MAX_BELLCOUNT_DAY];
        txtHours = new JTextField[MAX_BELLCOUNT_DAY];
        lblColons = new JLabel[MAX_BELLCOUNT_DAY];
        txtMinutes = new JTextField[MAX_BELLCOUNT_DAY];

        lblPoints[0] = lblPoint_1;
        chkUseFlags[0] = chkUseFlag_1;
        lblColons[0] = lblColon_1;
        txtHours[0] = txtHour_1;
        txtMinutes[0] = txtMinute_1;
        
        for (int i = 1; i < MAX_BELLCOUNT_DAY / 2; i++)
        {
        	Rectangle rt; int step = 30;
        	
        	lblPoints[i] = new JLabel(lblPoint_1.getText() + String.valueOf(i + 1) + " :");
        	rt = lblPoints[i - 1].getBounds(); 		rt.y += step;
        	lblPoints[i].setBounds(rt);
        	getContentPane().add(lblPoints[i]);
        	
        	chkUseFlags[i] = new JCheckBox();
        	rt = chkUseFlags[i - 1].getBounds();	rt.y += step;
        	chkUseFlags[i].setBounds(rt);
        	getContentPane().add(chkUseFlags[i]);
    	
        	txtHours[i] = new JTextField();
        	rt = txtHours[i - 1].getBounds();		rt.y += step;
        	txtHours[i].setBounds(rt);
        	getContentPane().add(txtHours[i]);

        	lblColons[i] = new JLabel(":");
        	rt = lblColons[i - 1].getBounds(); 		rt.y += step;
        	lblColons[i].setBounds(rt);
        	getContentPane().add(lblColons[i]);

        	txtMinutes[i] = new JTextField();
        	rt = txtMinutes[i - 1].getBounds();		rt.y += step;
        	txtMinutes[i].setBounds(rt);
        	getContentPane().add(txtMinutes[i]);
        }
        lblPoint_1.setText(lblPoint_1.getText() + "1 :");
        
        lblPoints[MAX_BELLCOUNT_DAY / 2] = lblPoint_13;
        chkUseFlags[MAX_BELLCOUNT_DAY / 2] = chkUseFlag_13;
        lblColons[MAX_BELLCOUNT_DAY / 2] = lblColon_13;
        txtHours[MAX_BELLCOUNT_DAY / 2] = txtHour_13;
        txtMinutes[MAX_BELLCOUNT_DAY / 2] = txtMinute_13;
        
        for (int i = MAX_BELLCOUNT_DAY / 2 + 1; i < MAX_BELLCOUNT_DAY; i++)
        {
        	Rectangle rt; int step = 30;
        	
        	lblPoints[i] = new JLabel(lblPoint_13.getText() + String.valueOf(i + 1) + " :");
        	rt = lblPoints[i - 1].getBounds(); 		rt.y += step;
        	lblPoints[i].setBounds(rt);
        	getContentPane().add(lblPoints[i]);
        	
        	chkUseFlags[i] = new JCheckBox();
        	rt = chkUseFlags[i - 1].getBounds();	rt.y += step;
        	chkUseFlags[i].setBounds(rt);
        	getContentPane().add(chkUseFlags[i]);
    	
        	txtHours[i] = new JTextField();
        	rt = txtHours[i - 1].getBounds();		rt.y += step;
        	txtHours[i].setBounds(rt);
        	getContentPane().add(txtHours[i]);

        	lblColons[i] = new JLabel(":");
        	rt = lblColons[i - 1].getBounds(); 		rt.y += step;
        	lblColons[i].setBounds(rt);
        	getContentPane().add(lblColons[i]);

        	txtMinutes[i] = new JTextField();
        	rt = txtMinutes[i - 1].getBounds();		rt.y += step;
        	txtMinutes[i].setBounds(rt);
        	getContentPane().add(txtMinutes[i]);
        }
        lblPoint_13.setText(lblPoint_13.getText() + "13 :");
	}
	
    private void btnRead_actionPerformed(ActionEvent evt) {
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
        
        dbBellSetting = SBXPCProxy.GetBellTime(SysUtil.MachineNumber, MAX_BELLCOUNT_DAY);
        
        if(dbBellSetting.isSuccess())
        {
            errorCode = 0;
            ShowBellSetting();
        }else
        {
            errorCode = (int)SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;
        }
        
        lblMessage.setText(SysUtil.ErrorPrint(errorCode));
        
        ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
    }

    private void btnWrite_actionPerformed(ActionEvent evt) {
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
        
        UIValue2Local();
        ret = SBXPCProxy.SetBellTime(SysUtil.MachineNumber, dbBellSetting.bellCount, dbBellSetting.bellInfoList);
        
        if(ret)
        {
            errorCode = 0;
            ShowBellSetting();
        }else
        {
            errorCode = (int)SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;
        }
        
        lblMessage.setText(SysUtil.ErrorPrint(errorCode));
        
        ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
        
    }

    private void ShowBellSetting()
    {
        if(dbBellSetting == null)
            return;
        txtBellCount.setText(String.valueOf(dbBellSetting.bellCount));
        if(dbBellSetting.bellInfoList == null)
            return;
        for(int i = 0; i < MAX_BELLCOUNT_DAY; i ++)
        {
            chkUseFlags[i].setSelected(dbBellSetting.bellInfoList[i] == 1);
            txtHours[i].setText(String.valueOf(dbBellSetting.bellInfoList[i + MAX_BELLCOUNT_DAY]));
            txtMinutes[i].setText(String.valueOf(dbBellSetting.bellInfoList[i + MAX_BELLCOUNT_DAY * 2]));
        }
    }
    
    private void UIValue2Local()
    {
        if(dbBellSetting == null)
            dbBellSetting = new GetBellTimeOutput();
        if(dbBellSetting.bellInfoList == null)
            dbBellSetting.bellInfoList = new byte[MAX_BELLCOUNT_DAY * 3];
        for(int i = 0; i < MAX_BELLCOUNT_DAY; i ++)
        {
            if(chkUseFlags[i].isSelected())
                dbBellSetting.bellInfoList[i] = 1;
            else
                dbBellSetting.bellInfoList[i] = 0;
            try{ dbBellSetting.bellInfoList[i + MAX_BELLCOUNT_DAY] = Byte.parseByte(txtHours[i].getText()); } catch(Exception e){}
            try{ dbBellSetting.bellInfoList[i + MAX_BELLCOUNT_DAY * 2] = Byte.parseByte(txtMinutes[i].getText()); } catch(Exception e){}
        }
        try{ dbBellSetting.bellCount = Long.parseLong(txtBellCount.getText()); } catch(Exception e){}
    }
    
}
