;; Name: 	 Johnathan Tang 
;; UCINetID: 63061294

ORG 0H            
CALL  MAIN ;; Immediatly go to Main label 


STRING1:  DB "test string one" ;; string data 
DB 0  ;; Null termination 
STRING1_L: DB 15

STRING2:  DB "test string two" ;; string data 
DB 0  ;; Null termination  
STRING2_L:  DB  15


;; ***************** TEST CASES *************************
;; -- uncomment to change value of strings and comment string 
;;	  values above 

; STRING1:  DB 0 ;; string data 
; DB 0  ;; Null termination 


; STRING1_L: DB 0
; STRING2:  DB "Hello World" ;; string data 
; DB 0  ;; Null termination  
; STRING2_L:  DB  11

; STRING1:  DB "a" ;; string data 
; DB 0  ;; Null termination 


; STRING1_L: DB 1
; STRING2:  DB "b" ;; string data 
; DB 0  ;; Null termination  
; STRING2_L:  DB  1

;; *******************************************************

STRCPY:
	MOV R1, #0

ITER: 
	INC R1		;;iterate through characters, given length until it reaches total length of 
	MOV A , #0
	MOVC A, @A + DPTR 
	MOV @R0, A

	INC DPTR		;; increment DPTR and R0 to iterate index 
	INC R0

	JNZ ITER	;; Done itering 
	MOV A, R1	;; move to Accumulator and return string 
	DEC A
	ljmp DONE_ITER 
	
	

GET_STRINGL: 

	MOV A, #0
	MOV DPTR, #STRING1_L	;; get length of string 1 
	MOVC A, @A+DPTR
	JZ ERROR 				;; if length is 0, error
	MOV R2, A
	
	MOV A, #0				;; get length of string 2  
	MOV DPTR, #STRING2_L
	MOVC A, @A+DPTR		
	JZ ERROR				;; if length is 0, error 
	ADD A, R2				;; add length of string1 and string2 
	MOV R2, A				
	ljmp STRCONCAT
	


STRCONCAT: 	
	;; store values in R0, DPL, DPH, and R1 (respectively) 
	;; increment stack pointer 
	PUSH 0		
	PUSH DPL
	PUSH DPH
	PUSH 1
	
	MOV DPTR, #STRING1	;; load string1 (address) to DPTR  
	CALL STRCPY_PUSH	;; push values to registers
	
	MOV DPTR, #STRING2	;; load string2 (address) to DPTR
	MOV R1, A
	ADD A , R0
	MOV R0, A 
	CALL STRCPY_PUSH
	ADD A, R1
	CALL GET_STRING	
	
GET_STRING: 		;; store value and decrement stack pointer 
	POP 1
	POP DPH
	POP DPL
	POP 0
	
	RET
	
STRCPY_PUSH:	;; store values to DPH, DPL, R0, and R1 (respectively) 
	PUSH DPH 
	PUSH DPL 
	PUSH 0 
	PUSH 1 
	ljmp STRCPY 
	
DONE_ITER: 
	POP 1 		;; after iterating, store value in R1, R0, DPL, and DPH respectively
	POP 0 
	POP DPL 
	POP DPH
	RET
	

TESTSTRING: 
	CALL STRCONCAT	;; Call STRCONCAT to get string data to concat 

	CJNE A, 02, ERROR	;; Check if expected string length equals what we stored in Accumulator
						;; if values are not equal, flag an error 
						
	JZ SUCCESS			;; concat success 

	MOV DPTR, #STRING1	
		
;; Main function 
MAIN: 
	;; Initialize and Clear registers
	MOV R0, #0 
	MOV R1, #0 
	MOV R2, #0 
	MOV R3, #0 
	
	;Assign #60h to R0 
	MOV R0, #60H
	;; Go to TESTSTRING
	LCALL TESTSTRING

;; If succcess, push 1 to R3
SUCCESS:
MOV R3, #1H 
SJMP SUCCESS 

;; If fail, push 2 to R3
ERROR: 
MOV  R3, #2H 
SJMP ERROR  
END

