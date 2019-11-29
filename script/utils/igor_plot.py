class igor_plt:
	def __init__(self,graph_name,xy_value,bandgap=False):
		self.graph_name=graph_name
		self.xy_value=xy_value
		self.plot=None
		self.single_plot_start()
		if len(xy_value)==1:
			pass
		elif len(xy_value)>1:
			self.multiple_plot()
		else:
			print("There's no x and y value for plotting!")
			raise ValueError('No xy_value')
		self.graph_option()
		if bandgap:
			self.bandgap=bandgap
			self.bandgap_plot()
		else:
			pass
		self.graph_end()
		return
	def graph_option(self):
		self.plot.write("X ModifyGraph mode=4\n")
		self.plot.write("X ModifyGraph marker=19,msize=5,mrkThick=2\n")
		self.plot.write("X ModifyGraph width=340.157,height=226.772\n")
		self.plot.write("X ModifyGraph tick=2,btLen=8,btThick=2\n")
		self.plot.write("X ModifyGraph tick(left)=2\n")
		self.plot.write("X ModifyGraph lsize=2\n")
		self.plot.write("X ModifyGraph rgb=(0,0,65535)\n")
		self.plot.write("X ModifyGraph mirror=1\n")
		self.plot.write("X ModifyGraph nticks(left)=3\n")
		self.plot.write("X ModifyGraph fSize=28\n")
		self.plot.write("X ModifyGraph lblMargin=15\n")
		self.plot.write("X ModifyGraph standoff=0\n")
		self.plot.write("X ModifyGraph axisOnTop=1\n")
		self.plot.write("X ModifyGraph axThick=2\n")
		self.plot.write('X ModifyGraph gFont="Times New Roman"\n')
		self.plot.write("X ModifyGraph gfSize=24\n")
		self.plot.write("X ModifyGraph zero(bottom)=8,zeroThick(bottom)=2\n")
		self.plot.write("X ModifyGraph noLabel=0\n")
		self.plot.write("X ModifyGraph grid(bottom)=0,gridHair(bottom)=0,gridStyle(bottom)=5,gridRGB(bottom)=(0,0,0)\n")
		self.plot.write('X Label bottom "Fermi Energy (eV)"\n')
		self.plot.write('X Label left "Defect formation energy(eV)"\n')
		self.plot.write("X SetAxis left 0,5\n")
		self.plot.write("X SetAxis bottom 0,4\n")
		return
	def single_plot_start(self):
		plot_data=self.xy_value[0]
		self.plot=open('%s.itx'%self.graph_name,'w')
		self.plot.write("IGOR\n")
		self.plot.write("WAVES/D ")
		data_name=plot_data[0]
		self.plot.write("%s_x %s_y\n"%(data_name,data_name))
		self.plot.write("BEGIN\n")
		for x,y in zip(plot_data[1],plot_data[2]):
			self.plot.write("%f %f\n"%(float(x),float(y)))
		self.plot.write("END\n")
		self.plot.write("X Display %s_y vs %s_x\n"%(data_name,data_name))
		return
	def multiple_plot(self):
		plot_data=self.xy_value[1:]
		for data in plot_data:
			self.plot.write("WAVES/D ")
			self.plot.write("%s_x %s_y\n"%(data[0],data[0]))
			self.plot.write("BEGIN\n")
			for x,y in zip(data[1],data[2]):
				self.plot.write("%f %f\n"%(float(x),float(y)))
			self.plot.write("END\n")
			self.plot.write("X AppendToGraph %s_y vs %s_x\n"%(data[0],data[0]))
		return
	def bandgap_plot(self):
		self.plot.write("WAVES/D ")
		self.plot.write("bandgap grid_line\n")
		self.plot.write("BEGIN\n")
		self.plot.write("%f -100\n"%float(self.bandgap))
		self.plot.write("%f 100\n"%float(self.bandgap))
		self.plot.write("END\n")
		self.plot.write("X AppendToGraph grid_line vs bandgap\n")
		self.plot.write("X ModifyGraph lsize=2,lstyle(grid_line)=7,rgb(grid_line)=(0,0,0)\n")
	def graph_end(self):
		self.plot.close()