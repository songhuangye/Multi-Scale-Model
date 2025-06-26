      SUBROUTINE USDFLD(FIELD,STATEV,PNEWDT,DIRECT,T,CELENT,
     1 TIME,DTIME,CMNAME,ORNAME,NFIELD,NSTATV,NOEL,NPT,LAYER,
     2 KSPT,KSTEP,KINC,NDI,NSHR,COORD,JMAC,JMATYP,MATLAYO,
     3 LACCFLA)
C
      INCLUDE 'ABA_PARAM.INC'
C
      CHARACTER*80 CMNAME,ORNAME
      CHARACTER*3  FLGRAY(15)
      DIMENSION FIELD(NFIELD),STATEV(NSTATV),DIRECT(3,3),
     1 T(3,3),TIME(2)
      DIMENSION ARRAY(15),JARRAY(15),JMAC(*),JMATYP(*),
     1 COORD(*)

C     # =================   START  ================= #
	  DOUBLE PRECISION F TEMP_TRANS, CTEMP	

C	  # Temperature that the change of field number happens
C	  # TEMP_TRANS in [°C] ORIGINAL = 1410
	  TEMP_TRANS = 1410	  

C	  # The temperature at the last increment will be saved as STATEV(1)
C	  # The CTEMP and LTEMP updated in every increment

	  CALL GETVRM('TEMP',ARRAY,JARRAY,FLGRAY,JRCD,JMAC,JMATYP,
     1     MATLAYO,LACCFLA)
	  CTEMP = TEMP
	  CTEMP = ARRAY(1)
	  
	  F = STATEV(4)
	  
	  IF (TIME(2) .EQ. 0.0) THEN
		  IF (F > 0.2) THEN
			  F = 1.0
		  ELSE
			  F = 0.0
		  END IF
	  ELSE
		  IF (CTEMP >= TEMP_TRANS .AND. F < 0.9) THEN
			  F = 1.0
		  ELSE
			  CONTINUE
		  END IF
	  END IF
	  
	  FIELD(1) = F
	  
	  STATEV(1) = F
	  
	  STATEV(4) = FIELD(1)
	  
      RETURN
      END 
	  
      SUBROUTINE DFLUX(FLUX,SOL,KSTEP,KINC,TIME,NOEL,NPT,COORDS,
     1 JLTYP,TEMP,PRESS,SNAME)
C
      INCLUDE 'ABA_PARAM.INC'
C
      DIMENSION FLUX(2), TIME(2), COORDS(3)
      CHARACTER*80 SNAME
      double precision alpha, p, x, y, z, r0, t, v, x0, y0, r1, pi
C	  time in seconds
	  t = TIME(2)
C	  pi number
	  pi = 3.1416
C	  defining postion parameters
	  x = coords(1)
	  y = coords(2)
	  z = coords(3) 
C	  alpha_R in the paper
	  alpha = 0.87

 

C  	  laser beam diameter [mm]
  	  r0 = 0.1
C	  power of the laser [mW]
  	  p = 160000.0*0.6
C	  beam velocity [mm/s]
      v = 900.0

C ============================================================================================== C 
C [1,0] / (-2.5, 2.5) --> (2.5, 2.5) / Direction  = (1.0,0.0) / Time = 0.005555555555555556 / Scanning
C ============================================================================================== C 
  	  IF (t <= 0.005555555555555556) THEN 
C     Layer-001, Track-000 (-2.5, 2.5) --> (2.5, 2.5) 
          x0 = v * (1.0) * t + -2.5
          y0 = v * (0.0) * t +  2.5
          r1 = ((x-x0)**2 + (y-y0)**2)**0.5 
          flux(1) = ((alpha*p)/(pi*r0**2))*exp(-(r1/r0)**2) 
          flux(2) = 0 
      ELSE 
          flux(1) = 0
          flux(2) = 0
      ENDIF 
      RETURN
      END
