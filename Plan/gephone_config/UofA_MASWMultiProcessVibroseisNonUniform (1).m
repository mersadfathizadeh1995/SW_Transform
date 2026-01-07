%       Written by:  Clinton Wood   2008
%       Filename:    UofA_MASWMultiProcess.m
%       Updated:     4-15-15
%
%       This matlab file was designed to analyze MASW data using a
%       Frequency-Wavenumber Analysis and eliminate none fundamental mode
%       dispersion data.
%
%       Input  
%       The Linear Spectrum between of each receiver.
%       The Source offset from the first sensor.
%       The uniform spacing between each sensor measured from the source.
%       Number of offsets collected at site.
%       
%       Output 
%       Plots of the 3-D f-k spectra and 3-D dispersion curve.
%       Data elimination process plot
%       Raw data in dispdata.mat
%       Fit data in Forwardmodeling.mat
%       
%       This code was developed for the University of Arkansas.
%
%       
%       Reference:
%
%           Hebeler, Gregory L. & Rix, Glenn J. (2001).  "Site
%           Characterization in Shelby County, Tennessee using Advanced
%           Surface Wave Methods."
%           Report for Mid-America Earthquake Center Release 06-02.


files=[1;2;3;4];           %Enter the files to be processed
offset=[5;10;20;40];    %Enter source offset 
Filetype=2;          %Enter file type to be analyzed (1 for Spectrum and 
                     % 2 for transfer functions, 3 for average time records
                     % 4 for seg files from geode, 5 for seg files with 
                     % individual averages)
Shaker=0;             %Enter 1 if shaker and Quattro were used with Geode 


spacing=[0;2;4;6;8;10;14;18;22;26;30;35;40;45;50;55;60;65;70;75;80;85;90;95];           %Enter the spacing between geophones
numk=4000;            % Number of trial wavenumbers
numf=4000;            %Number of frequency domain points
numcon=5;           %Number of contour lines for 3-D plots
timelength=1;       %Enter the signal length in seconds
max_velocity=5000;  % Enter the maximum velocity plotted on the dispersion curve
max_frequency=100;   % Enter the maximum frequency plotted on the 3-D f-k spectra and dispersion curve
max_wavelength=500;  % Enter the maximum wavelength plotted on the 2-D Dispersion curve
numchannels=24;


Plot_flag=0;          %Controls Plotting of Spatiospectral correlation matrix (Yes=1 No=0) 
Plot_flag3D=0;        % Controls 3-D plotting of wavenumber 
Plot_flag3Dfr=1;      % Controls plotting of 3-D Frequency figure
Plot_flag3Dwave=0;    % Controls plotting of 3-D wavelength figure
Plot_flag3Dwf=0;


%%
tic
L=waitbar(0,'Loop Progress');
scrsz = get(0,'ScreenSize');  
if Filetype==1
    name='G';
elseif Filetype==2
    name='G25_';
elseif Filetype==3
    name='A';    
end

numfiles=length(files);

for a=1:numfiles

    current=files(a,1); 
if Filetype<4
if current<10
       datatitle= 'DPsv0000'; 
    elseif current<100
       datatitle= 'DPsv000';
    else 
       datatitle= 'DPsv00';
end
    
filename=[datatitle,num2str(current),'.mat']; 
% Load the file which creates a structure of the data and allows us to 
% perform operations on the data.
dataStruc = load(filename);
end

if Filetype<3
% Use the frequency of the first channel in Hz.  
%The frequency is the same for each of the channels.
freq = dataStruc.([name,int2str(1)])(:,1); 

% Create a matrix of the cross power spectra between each geophone.
% This matrix contains phase data in imaginary number format.
   
TFMatrix = zeros( length(freq), numchannels );

for i = 1 : numchannels
	TFMatrix(:,i) = dataStruc.([name, int2str(i)])(:,2);
end

for i=1:numchannels
    for j=1:numchannels
        R(j,i,:)=TFMatrix(:,i)./TFMatrix(:,j);
    end
end

end

if Filetype==3 
    Timematrix=[dataStruc.A1(:,2) dataStruc.A2(:,2) dataStruc.A3(:,2)...
        dataStruc.A4(:,2) dataStruc.A5(:,2) dataStruc.A6(:,2)...
        dataStruc.A7(:,2) dataStruc.A8(:,2) dataStruc.A9(:,2)...
    dataStruc.A10(:,2) dataStruc.A11(:,2) dataStruc.A12(:,2) ...
    dataStruc.A13(:,2) dataStruc.A14(:,2) dataStruc.A15(:,2)...
    dataStruc.A16(:,2) dataStruc.A17(:,2) dataStruc.A18(:,2)...
    dataStruc.A19(:,2) dataStruc.A20(:,2) dataStruc.A21(:,2) ...
    dataStruc.A22(:,2) dataStruc.A23(:,2) dataStruc.A24(:,2)];

Startpoint=find(dataStruc.A1(:,1)==-0.0520833333333335); %  -0.099609375000000
Endpoint=find(dataStruc.A1(:,1)==timelength);  %0.201171875000000

deltat=dataStruc.A1(2,1)-dataStruc.A1(1,1);


if PlotStoN
%Signal to Noise calculations
%Signal
Numzeros=(numf*2-length(Timematrix))-1;
SignalTime=[Timematrix(Startpoint:Endpoint,:);zeros(Numzeros,numchannels)];

FreqS=fft(SignalTime);


N=length(FreqS);
n=length(FreqS);
deltaf=1/n/deltat;
nyq=1/deltat/2;
Frequency=[0:deltaf:nyq-deltaf]';
FreqMagS=(2/N)*abs(FreqS(1:length(Frequency),:));
FreqSM=smooth(mean(FreqMagS,2),101,'moving');

%Noise
NoiseTime=[Timematrix(Endpoint+2000:Endpoint+(Endpoint-Startpoint)+2000,:);zeros(Numzeros,numchannels)];
FreqN=fft(NoiseTime);

FreqMagN=(2/N)*abs(FreqN(1:length(Frequency),:));
FreqNM=smooth(mean(FreqMagN,2),101,'moving');

StoN(:,a)=10*log10(FreqSM./FreqNM);  

end


                                  


Timematrix=Timematrix(Startpoint:Endpoint,:);
Numzeros=(numf*2-length(Timematrix))-1;
Timematrix=[Timematrix; zeros(Numzeros,numchannels)];




elseif Filetype==4
    filename=[num2str(current),'.dat'];
    
    %Calls seg2load function
    [time,Timematrix,Shotpoint,Spacing,deltat,delay] = seg2loadTX (filename);
    
if Shaker
Startpoint=1;
Endpoint=find(time==max(time));
else
Startpoint=find(time==0);
Endpoint=find(time==timelength);
end


Timematrix=Timematrix(Startpoint:Endpoint,:);
Numzeros=(numf*2-length(Timematrix))-1;
Timematrix=[Timematrix; zeros(Numzeros,numchannels)];    
elseif Filetype==5
 filename=['save',num2str(current),'.mat'];   
 load(filename)   
    
end


if Filetype>2
    
    blocklength=length(Timematrix);
    fs=1/(deltat);
% Create a matrix of the cross power spectra between each geophone.
% This matrix contains phase data in imaginary number format.
clear R
%R = zeros( numchannels, numchannels, blocklength/2+1);

for m=1:numchannels
    for n=1:numchannels
        [R(n,m,:) freq1]=cpsd(Timematrix(:,m),Timematrix(:,n),rectwin(blocklength),0,blocklength,fs); 
    end
end 




  fpr=abs(freq1-10);
  setf10=find(fpr==min(fpr));
  fpt=abs(freq1-max_frequency);
setfmax=find(fpt==min(fpt));
divd=round((length(freq1)-setf10)/400);
if divd<1
    divd=1;
end
tra=[1:setf10,setf10+1:divd:setfmax];

R=R(:,:,tra);
freq=freq1(tra,:); 
end





%% Start processing
%Plots the Spatiospectral Correlation Matrix if Plot_flag =1 above. 

if Plot_flag
    h1=figure; hold on;
    for m=1:numchannels
        for n=1:numchannels
            subplot(numchannels,numchannels,numchannels*(m-1)+n)
            plot(freq,(180/pi)*angle(squeeze(R(m,n,:))));
            set(gca,'xlim',[0 200],'ylim',[-180,180],'xticklabel',...
                '','yticklabel','','fontsize',2);
        
                if n==1 && m==fix(numchannels/2)
                    ylabel('Cross Spectra Phase (Degrees)','Fontsize',12);
                end
            if m==numchannels && n== fix(numchannels/2)
                xlabel('frequency (Hz)','Fontsize',12);
            end
            drawnow;
        end
    end
end

%Compute the position of each geophone for the Beamformer Analysis

position=zeros(numchannels,2);
    
    position(:,1)=spacing;
   
    




% Define the maximum wavenumber to avoid spatial aliasing
kalias=pi./(min(abs(diff(position(:,1)/2))));

%Define a vector of trial wavenumbers
ktrial=linspace(0.0001,kalias,numk);

% Allocate matrix for beamforming. 
Power = zeros(numk, length(freq));
pnorm = zeros(numk, length(freq));
kmax = zeros(length(freq),1);

%Calculate the f-k spectrum using the 1-D beamforming method 
%(e)=Steering vector 
%Normalize the f-k spectrum to allow for 3-d plotting
%Select the maximum value at each frequency for single point dispersion
for i=1:length(freq)
    for j=1:numk
        expterm=exp(1i * ktrial(j) * position(:,1));
        Power(j,i)=expterm'*R(:,:,i)*expterm;
    end
    [max_value,max_index]=max(abs(Power(:,i)));
    pnorm(:,i)=Power(:,i)/max_value;
    kmax(i)=ktrial(max_index);
end


% Calculates the maximum velocity for each frequency    
vmax=2*pi*freq./kmax;

% Calculates the Maximum Wavelength for each frequency
Wavelength=vmax./freq;

%Plot the 3-D f-k spectra

[fr wave]=meshgrid(freq,ktrial);

velocity=2*pi*fr./wave;

waveLE=(1./wave)*2*pi;

if Plot_flag3D
figure('outerPosition',[scrsz(1) scrsz(2) scrsz(3) scrsz(4)])

contourf(wave,fr,pnorm,numcon);
colormap(jet);
set(gca,'Ylim',[0 max_frequency],'xlim',[0,kalias],'xminortick','on',...
    'yminortick','on','tickdir','out');   
xlabel('Wavenumber (rad/m)');
ylabel('Frequency (Hz)');
title('3-D f-k Spectra','FontWeight','bold','FontSize',14);
hold on;
plot(kmax',freq,'ow');

hold off;

end

if Plot_flag3Dwf
figure('outerPosition',[scrsz(1) scrsz(2) scrsz(3) scrsz(4)])

contourf(fr,waveLE,pnorm,numcon);
colormap(jet);
set(gca,'Ylim',[0 500],'xlim',[0,200],'xminortick','on',...
    'yminortick','on','tickdir','out');   
xlabel('Frequency (Hz)');
ylabel('Wavelength (m)');
title('3-D f-k Spectra','FontWeight','bold','FontSize',14);
hold on;
plot(freq,Wavelength,'ow');

hold off;

saveas(gcf,'wf.jpg')

end    
    
    
    

if Plot_flag3Dfr 
%plot the 3-D dispersion curve
figure1=figure('outerPosition',[scrsz(1) scrsz(2) scrsz(3) scrsz(4)]);
axes1 = axes('Parent',figure1,'YMinorTick','on',...
    'XMinorTick','on',...
    'TickDir','in',...
    'Layer','top',...
        'FontSize',16,...
    'FontName','Times New Roman');
box(axes1,'on');
hold(axes1,'all');
contourf(fr,velocity,real(pnorm),numcon);
colormap(jet);
set(gca,'Ylim',[0 max_velocity],'xlim',[1,max_frequency]);
xlabel('Frequency (Hz)','FontSize',16,'FontName','Times New Roman');
ylabel('Phase Velocity (m/sec)','FontSize',16,'FontName','Times New Roman');

hold on;
plot(freq,vmax','ow');

hold off;
end

if Plot_flag3Dwave
figure1=figure('outerPosition',[scrsz(1) scrsz(2) scrsz(3) scrsz(4)]);
axes1 = axes('Parent',figure1,'YMinorTick','on','XScale','log',...
    'XMinorTick','on',...
    'TickDir','out',...
    'FontSize',16,...
    'FontName','Times New Roman');



box(axes1,'on');
hold(axes1,'all');
contourf(waveLE,velocity,pnorm,numcon);
colormap(jet);
set(gca,'Ylim',[0 max_velocity],'xlim',[spacing*2,max_wavelength]);
xlabel('Wavelength (m)','FontSize',16,'FontName','Times New Roman');


ylabel('Phase Velocity (m/sec)',...
    'FontSize',16,'FontName','Times New Roman');
  

hold on;
semilogx(Wavelength,vmax','ow');

hold off;

saveas(gcf,[num2str(offset(a,1)),' m offset']);


end


dispdata=[vmax,freq,Wavelength];


VelocityRaw(:,a)=vmax;
FrequencyRaw(:,a)=freq;
WavelengthRaw(:,a)=Wavelength;



 

waitbar(a/numfiles)
end


save('dispdata','VelocityRaw','FrequencyRaw','WavelengthRaw');

close(L)
toc




    
 [deleteVel]=find(VelocityRaw>max_velocity);
    VelocityRaw(deleteVel)=max_velocity; 
    
 [deleteWave]=find(WavelengthRaw>max_wavelength);
    WavelengthRaw(deleteWave)=2;
    
y=VelocityRaw(:);
x=FrequencyRaw(:);
z=WavelengthRaw(:);    


%Set plot size to full screen and plot figure.
scrsz = get(0,'ScreenSize');
figure('outerPosition',[scrsz(1) scrsz(2) scrsz(3) scrsz(4)])

%plots colors blue,green,red,black,cyan,magenta,yellow

s={'ro' 'bo' 'go' 'mo' 'ko' 'co' 'yo'};
ax(1)=subplot(1,2,1);
for r=1:numfiles
plot(FrequencyRaw(:,r),VelocityRaw(:,r),s{r},'markersize',7)
hold on
end
set(gca,'xminortick','on','yminortick','on','tickdir','out');
xlabel('Frequency (Hz)');
ylabel('Phase Velocity (m/sec)');
plot(x,y,'w.','markersize',1);

ax(2)=subplot(1,2,2);
for r=1:numfiles
semilogx(WavelengthRaw(:,r),VelocityRaw(:,r),s{r},'markersize',7)
hold on
end
semilogx(x,z,'w.','markersize',1);
set(gca,'xminortick','on','yminortick','on','tickdir','out');
xlabel('Wavelength (m)');
ylabel('Phase Velocity (m/sec)');
legend(num2str(offset),'location','best');



