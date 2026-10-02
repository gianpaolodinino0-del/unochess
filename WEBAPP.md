# UNO Chess online

La versione web riutilizza il motore Python del gioco desktop. È pensata per una partita privata tra due persone e si adatta anche a schermi Android. A ogni partita i colori Bianco e Nero vengono assegnati a sorte.

## Avvio sul PC

```powershell
py -m pip install -r requirements.txt
py webapp.py
```

Apri `http://localhost:5000`. Per provare da un telefono collegato alla stessa rete Wi-Fi, apri `http://IP-DEL-PC:5000` sul telefono.

## Pubblicazione gratuita su Render

Il repository include `render.yaml` per creare un servizio web Python sul piano gratuito di Render:

1. Installa GitHub Desktop e scegli **File → Add local repository**, selezionando questa cartella. Se non è ancora un repository Git, scegli l'opzione per crearne uno qui; poi fai il primo commit e **Publish repository**.
2. In Render scegli **New → Blueprint**, collega GitHub e seleziona il repository appena pubblicato.
3. Conferma la creazione del servizio `unichess` definito in `render.yaml`.
4. Quando il deploy è finito, apri l'indirizzo HTTPS `onrender.com`, crea una stanza e premi **Copia link invito**. Il link inviterà direttamente il tuo amico da qualsiasi rete.

Render assegna al servizio un indirizzo `onrender.com` pubblico, quindi i due giocatori possono collegarsi anche da reti e IP diversi. Il piano gratuito sospende il servizio dopo 15 minuti senza richieste; alla successiva apertura può impiegare circa un minuto a ripartire. Le stanze restano in memoria, quindi un riavvio del servizio richiede di creare una nuova partita.

## Su Android

Apri l'indirizzo HTTPS in Chrome. Dal menu ⋮ scegli **Aggiungi a schermata Home** o **Installa app**. Poi crea una stanza e invia il link invito al secondo giocatore.
