# UNO Chess — Specifica

## Obiettivo
Gioco per 2 giocatori che combina scacchi e UNO.

## Mazzo
- Carte numeriche: 1–8, 2 copie per colore.
- +2: 2 per colore.
- Stop: 2 per colore.
- Wild: 4.
- +4: 4.
- Totale: 88 carte.

## Inizio partita
- Ogni giocatore riceve 7 carte.
- La prima carta scoperta deve essere numerica.
- Il colore attivo iniziale è quello della prima carta.

## Compatibilità delle carte
Una carta può essere giocata se:
- ha lo stesso colore della carta attiva; oppure
- ha lo stesso valore; oppure
- è Wild/+4.

## Carte numeriche
Una carta numerica N abilita le mosse degli scacchi:
- dalla riga N; oppure
- dalla colonna N.
La numerazione delle righe/colonne deve essere definita coerentemente nell'implementazione.

## Wild
- Non impone direttamente una mossa.
- Il giocatore sceglie il nuovo colore.
- Il nuovo colore diventa quello attivo.

## +2
- L'avversario deve pescare 2 carte.
- In una partita a 2 giocatori, il turno torna al giocatore che ha giocato il +2.

## Stop
- Salta il turno dell'avversario.
- In una partita a 2 giocatori, il turno torna al giocatore che ha giocato lo Stop.

## +4
- L'avversario pesca 4 carte.
- Il giocatore sceglie il nuovo colore.
- In una partita a 2 giocatori, il turno torna al giocatore che ha giocato il +4.

## Pesca
- Non deve esistere un loop in cui il giocatore deve premere ripetutamente "pesca".
- Se non esiste una carta utile, la pesca deve essere gestita automaticamente.
- Una carta pescata utilizzabile deve poter essere giocata immediatamente.

## Scacchi
- Le mosse devono essere generate tramite python-chess.
- Le carte determinano quali mosse sono disponibili.
- Quando il Re è sotto scacco, le regole UNO continuano ad applicarsi alle mosse disponibili.
- Il Re non viene mai materialmente catturato.

## Vittoria
La partita termina quando:
1. si verifica uno scacco matto secondo le regole del gioco; oppure
2. il Re avversario sarebbe catturabile secondo le regole UNO/Chess.

## Separazione del codice
Backend:
- regole UNO
- stato partita
- integrazione scacchi
- turni
- vittoria

Frontend:
- visualizzazione
- input del giocatore
- dialoghi

QA:
- test automatici
- verifica delle regole
- riproduzione dei bug
- nessuna modifica al codice di Backend/Frontend salvo richiesta del Coordinatore.