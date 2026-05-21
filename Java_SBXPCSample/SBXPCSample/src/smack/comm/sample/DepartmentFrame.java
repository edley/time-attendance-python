package smack.comm.sample;

import java.awt.EventQueue;
import java.awt.Font;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.text.DecimalFormat;
import java.text.NumberFormat;

import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JTextField;
import javax.swing.SwingConstants;

import smack.comm.SBXPCProxy;
import smack.comm.output.OneStringOutput;
import smack.comm.sample.global.SysUtil;

import javax.swing.JList;
import javax.swing.AbstractListModel;
import javax.swing.JButton;
import java.awt.event.ActionListener;
import java.awt.event.ActionEvent;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import javax.swing.ListSelectionModel;
import javax.swing.JScrollPane;

public class DepartmentFrame extends JFrame {
	private JLabel lblMessage;
    private JScrollPane jScrollPane1;
	private JLabel lblDepartmentName;
	private JTextField txtDepartment;
	private JList lstDepartment;
	private JButton btnUpdate;
	private JButton btnRead;
	private JButton btnWrite;

    DepartmentListModel listModel = new DepartmentListModel();

	/**
	 * Launch the application.
	 */
	public static void main(String[] args) {
		EventQueue.invokeLater(new Runnable() {
			public void run() {
				try {
					DepartmentFrame frame = new DepartmentFrame();
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
	public DepartmentFrame() {
		addWindowListener(new WindowAdapter() {
			@Override
			public void windowClosing(WindowEvent arg0) {
				if (MainFrame.getInstance() != null)
					MainFrame.getInstance().setVisible(true);
			}
		});
		
		setTitle("Department");
		setBounds(100, 100, 522, 547);
		setDefaultCloseOperation(javax.swing.WindowConstants.DISPOSE_ON_CLOSE);
		getContentPane().setLayout(null);
		
		lblMessage = new JLabel("Message");
		lblMessage.setHorizontalAlignment(SwingConstants.CENTER);
		lblMessage.setFont(new Font("Segoe UI", Font.BOLD, 18));
		lblMessage.setBorder(javax.swing.BorderFactory.createBevelBorder(javax.swing.border.BevelBorder.LOWERED));
		lblMessage.setBounds(10, 11, 479, 40);
		getContentPane().add(lblMessage);
		
		lblDepartmentName = new JLabel("Department Name:");
		lblDepartmentName.setBounds(10, 75, 112, 14);
        getContentPane().add(lblDepartmentName);
		
		txtDepartment = new JTextField();
		txtDepartment.setBounds(138, 72, 117, 20);
		getContentPane().add(txtDepartment);
		txtDepartment.setColumns(10);
		
		lstDepartment = new JList();
        lstDepartment.setModel(listModel);
        lstDepartment.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
		lstDepartment.addMouseListener(new MouseAdapter() {
			@Override
			public void mouseClicked(MouseEvent arg0) {
				lstDepartmentMouseClicked(arg0);
			}
		});
		lstDepartment.setBounds(26, 117, 364, 369);
		//getContentPane().add(lstDepartment);

		jScrollPane1 = new JScrollPane();
		jScrollPane1.setBounds(10, 119, 380, 378);
        jScrollPane1.setViewportView(lstDepartment);
		getContentPane().add(jScrollPane1);

	
		btnUpdate = new JButton("Update");
		btnUpdate.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnUpdate_actionPerformed(arg0);
			}
		});
		btnUpdate.setBounds(400, 117, 89, 23);
		getContentPane().add(btnUpdate);
		
		btnRead = new JButton("Read");
		btnRead.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnRead_actionPerformed(arg0);
			}
		});
		btnRead.setBounds(400, 360, 89, 23);
		getContentPane().add(btnRead);
		
		btnWrite = new JButton("Write");
		btnWrite.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				btnWrite_actionPerformed(arg0);
			}
		});
		btnWrite.setBounds(400, 404, 89, 23);
		getContentPane().add(btnWrite);
		
	}
	
	public class DepartmentName
    {
        public final int index;
        public String departmentName;

        public DepartmentName(int index)
        {
            this.index = index;
            this.departmentName = "";
        }

        @Override
        public String toString()
        {
            NumberFormat formatter = new DecimalFormat("00");
            String ret = "[No.] " + formatter.format(this.index) + " ";
            ret = ret + "[Name] " + this.departmentName;
            return ret;
        }
    }
	 public class DepartmentListModel extends AbstractListModel
	    {
	        public static final int DEPT_COUNT = 20;
	        DepartmentName[] departmentNameList = new DepartmentName[DEPT_COUNT];

	        public DepartmentListModel()
	        {
	            for (int i = 0; i < DEPT_COUNT; i++)
	            this.departmentNameList[i] = new DepartmentName(i);
	        }

	        public void setElementAt(int index, String departmentName)
	        {
	            if ((index < 0) || (index >= DEPT_COUNT))
	                return;
	            this.departmentNameList[index].departmentName = departmentName;
	            fireContentsChanged(this, index, index);
	        }

	        @Override
	        public int getSize() {
	            return DEPT_COUNT;
	        }

	        @Override
	        public Object getElementAt(int index) {
	            return this.departmentNameList[index];
	        }
	    }

	  private void btnRead_actionPerformed(ActionEvent evt) {
	        boolean ret;
	        int errorCode;
	        
	        lblMessage.setText("Working...");
	        invalidate();

	        ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, false);

	        if (!ret)
	        {
	            this.lblMessage.setText("No Device");
	            return;
	        }

	        for (int i = 0; i < DepartmentListModel.DEPT_COUNT; i++)
	        {
	            OneStringOutput output = SBXPCProxy.GetDepartName(SysUtil.MachineNumber, i, 0L);
	            if (output.isSuccess())
	            {
	                this.listModel.setElementAt(i, output.value);
	                errorCode = 0;
	            }else {
	                errorCode = (int)SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;
	            }
	            this.lblMessage.setText(SysUtil.ErrorPrint(errorCode));
	        }

	        ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
	    }

	    private void btnWrite_actionPerformed(ActionEvent evt) {
	        boolean ret;
	        int errorCode = 0;
	        
	        lblMessage.setText("Working...");
	        invalidate();

	        ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, false);

	        if (!ret)
	        {
	            this.lblMessage.setText("No Device");
	            return;
	        }

	        for (int i = 0; i < DepartmentListModel.DEPT_COUNT; i++)
	        {
	            DepartmentName depart = (DepartmentName)this.listModel.getElementAt(i);
	            ret = SBXPCProxy.SetDepartName(SysUtil.MachineNumber, i, 0, depart.departmentName);
	            if (ret)
	                errorCode = 0;
	            else
	                errorCode = (int)SBXPCProxy.GetLastError(SysUtil.MachineNumber).dwValue;
	        }
	            
	        this.lblMessage.setText(SysUtil.ErrorPrint(errorCode));
	        
	        ret = SBXPCProxy.EnableDevice(SysUtil.MachineNumber, true);
	    }
	   
	    private void lstDepartmentMouseClicked(java.awt.event.MouseEvent evt) {
	        DepartmentName depart = (DepartmentName)lstDepartment.getSelectedValue();
	        txtDepartment.setText(depart.departmentName);
	    }

	    private void btnUpdate_actionPerformed(ActionEvent evt) {
	        listModel.setElementAt(lstDepartment.getSelectedIndex(), txtDepartment.getText());
	    }
}
