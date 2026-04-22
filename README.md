[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/SsfEgNPI)

Catalin a scris aici

## Server (Student A) — rulare

- **TCP (Misiunea A):** `python server/tcp_server.py --host <IP_ZeroTier> --port 5000`
- **UDP (Misiunea B):** `python server/udp_server.py --host <IP_ZeroTier> --port 5001`

Opțional: setează `ZT_HOST` și/sau `PORT` în mediu în loc de argumente.

## Protocol pentru client (Student B, alt limbaj)

- **Codificare:** UTF-8 peste tot.
- **TCP:** un mesaj text = o linie terminată cu `\n` (LF). Serverul răspunde cu linii `OK <text_primit>\n`.
- **UDP:** un datagram = un mesaj text UTF-8 care conține numărul secvenței (ex. `42` sau `MSG 42`). Serverul așteaptă id-uri distincte de la `1` la `100` (implicit); mesajele duplicate sau în afara intervalului sunt numărate separat.

## Întrebare finală (Wireshark — închidere conexiune TCP)

**Care sunt flag-urile TCP observate la `.close()`?**

_(Completează aici după captură: de obicei vei vedea schimb de segmente **FIN** și confirmări **ACK**; uneori **RST** dacă conexiunea e închisă brusc. Notează exact ce apare la tine.)_
