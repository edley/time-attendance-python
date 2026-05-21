package smack.comm.sample;

import java.awt.EventQueue;
import java.awt.Font;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.text.DecimalFormat;
import java.text.NumberFormat;

import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JScrollPane;
import javax.swing.JTextField;
import javax.swing.AbstractListModel;
import javax.swing.JButton;
import javax.swing.JList;
import javax.swing.ListSelectionModel;
import javax.swing.SwingConstants;

import smack.comm.SBXPCProxy;
import smack.comm.output.OneStringOutput;
import smack.comm.sample.global.SysUtil;

import java.awt.event.ActionListener;
import java.awt.event.ActionEvent;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;

public class ProxyFrame extends JFrame {
	private JLabel lblMessage;
	private JScrollPane scrollPane;
	private JLabel lblProxyName;
	private JTextField txtProxyName;
	private JButton btnUpdate;
	private JButton btnRead;
	private JButton btnWrite;
	private JList lstProxy;

    ProxyNameListModel listModel = new ProxyNameListModel();

	/**
	 * Launch the application.
	 */
	public static void main(String[] args) {
		EventQueue.invokeLater(new Runnable() {
			public void run() {
				try {
					ProxyFrame frame = new ProxyFrame();
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
	public ProxyFrame() {
		addWindowListener(new WindowAdapter() {
			@Override
			public void windowClosing(WindowEvent arg0) {
				if (MainFrame.getInstance() != null)
					MainFrame.getInstance().setVisible(true);
			}
		});
	
		setTitle("Proxy (DaiGong)");
		setBounds(100, 100, 488, 487);
		setDefaultCloseOperation(javax.swing.WindowConstants.DISPOSE_ON_CLOSE);
		getContentPane().setLayout(null);
		
		lblMessage = new JLabel("Message");
		lblMessage.setHorizontalAlignment(SwingConstants.CENTER);
		lblMessage.setFont(new Font("Segoe UI", Font.BOLD, 18));
		lblMessage.setBorder(javax.swing.BorderFactory.createBevelBorder(javax.swing.border.BevelBorder.LOWERED));
		lblMessage.setBounds(10, 11, 451, 40);
		getContentPane().add(lblMessage);
		
		scrollPane = new JScrollPane();
		scrollPane.setBounds(10, 104, 352, 328);
		getContentPane().add(scrollPane);
		
		lstProxy = new JList();
		lstProxy.addMouseListener(new MouseAdapter() {
			@Override
			public void mouseClicked(MouseEvent arg0) {
				lstProxyMouseClicked(arg0);
			}
		});
		lstProxy.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
		scrollPane.setViewportView(lstProxy);

        lstProxy.setModel(listModel);
		
		lblProxyName = new JLabel("Proxy Name : ");
		lblProxyName.setBounds(10, 76, 108, 14);
		getContentPane().add(lblProxyName);
		
		txtProxyName = new JTextField();
		txtProxyName.setBounds(128, 73, 234, 20);
		getContentPane().add(txtProxyName);
		txtProxyName.setColumns(10);
		
		btnUpdate = new JButton("Update");
		btnUpdate.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnUpdateMouseClicked(arg0);
			}
		});
		btnUpdate.setBounds(372, 102, 89, 23);
		getContentPane().add(btnUpdate);
		
		btnRead = new JButton("Read");
		btnRead.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnReadMouseClicked(arg0);
			}
		});
		btnRead.setBounds(372, 311, 89, 23);
		getContentPane().add(btnRead);
		
		btnWrite = new JButton("Write");
		btnWrite.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnWriteMouseClicked(arg0);
			}
		});
		btnWrite.setBounds(372, 362, 89, 23);
		getContentPane().add(btnWrite);

	}

	private void lstProxyMouseClicked(java.awt.event.MouseEvent evt) {
        ProxyName depart = (ProxyName)lstProxy.getSelectedValue();
        txtProxyName.setText(depart.proxyName);
    }

    private void btnUpdateMouseClicked(ActionEvent evt) {
        listModel.setElementAt(lstProxy.getSelectedIndex(), txtProxyName.getText());
    }

    private void btnReadMouseClicked(ActionEvent evt) {
        boolean ret;
        int errorCode;
        
        lblMessage.setText("Working...");
        invalidate();
        
        ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, false);
        
        if (!ret) {
            this.lblMessage.setText("No Device");
            return;
        }
        
        for (int i = 0; i < ProxyNameListModel.PROXY_COUNT; i++) {
            OneStringOutput output = SBXPCProxy.GetDepartName(SysUtil.MachineNumber, i + 1, 1L);
            if (output.isSuccess()) {
                this.listModel.setElementAt(i, output.value);
                errorCode = 0;
            }else {
                errorCode = (int)SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;
            }
            this.lblMessage.setText(SysUtil.ErrorPrint(errorCode));
        }
        
        ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
    }

    private void btnWriteMouseClicked(ActionEvent evt) {
        boolean ret;
        int errorCode = 0;
        
        lblMessage.setText("Working...");
        invalidate();
        
        ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, false);
        
        if (!ret) {
            this.lblMessage.setText("No Device");
            return;
        }
        
        for (int i = 0; i < ProxyNameListModel.PROXY_COUNT; i++) {
            ProxyName depart = (ProxyName)this.listModel.getElementAt(i);
            ret = SBXPCProxy.SetDepartName(SysUtil.MachineNumber, i + 1, 1, depart.proxyName);
            if (ret)
                errorCode = 0;
            else
                errorCode = (int)SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;
        }
        
        this.lblMessage.setText(SysUtil.ErrorPrint(errorCode));
        
        ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
    }

	 public class ProxyNameListModel extends AbstractListModel
	    {
	        public static final int PROXY_COUNT = 20;
	        ProxyName[] proxyNameList = new ProxyName[PROXY_COUNT];

	        public ProxyNameListModel()
	        {
	            for (int i = 0; i < PROXY_COUNT; i++)
	            this.proxyNameList[i] = new ProxyName(i);
	        }

	        public void setElementAt(int index, String proxyName)
	        {
	            if ((index < 0) || (index >= PROXY_COUNT))
	                return;
	            this.proxyNameList[index].proxyName = proxyName;
	            fireContentsChanged(this, index, index);
	        }

	        @Override
	        public int getSize() {
	            return PROXY_COUNT;
	        }

	        @Override
	        public Object getElementAt(int index) {
	            return this.proxyNameList[index];
	        }
	    }

	    public class ProxyName
	    {
	        public final int index;
	        public String proxyName;

	        public ProxyName(int index)
	        {
	            this.index = index;
	            this.proxyName = "";
	        }

	        @Override
	        public String toString()
	        {
	            NumberFormat formatter = new DecimalFormat("00");
	            String ret = "[No.] " + formatter.format(this.index) + " ";
	            ret = ret + "[Name] " + this.proxyName;
	            return ret;
	        }
	    }
}
