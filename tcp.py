import asyncio
import os
from tcputils import *


class Servidor:
    def __init__(self, rede, porta):
        self.rede = rede
        self.porta = porta
        self.conexoes = {}
        self.callback = None
        self.seq_no = os.urandom()
        self.ack_no = self.seq_no + 1
        self.rede.registrar_recebedor(self._rdt_rcv)

    def registrar_monitor_de_conexoes_aceitas(self, callback):
        """
        Usado pela camada de aplicação para registrar uma função para ser chamada
        sempre que uma nova conexão for aceita
        """
        self.callback = callback

    def _rdt_rcv(self, src_addr, dst_addr, segment):
        src_port, dst_port, seq_no, ack_no, \
            flags, window_size, checksum, urg_ptr = read_header(segment)

        if dst_port != self.porta:
            # Ignora segmentos que não são destinados à porta do nosso servidor
            return
        if not self.rede.ignore_checksum and calc_checksum(segment, src_addr, dst_addr) != 0:
            print('descartando segmento com checksum incorreto')
            return

        payload = segment[4*(flags>>12):]
        id_conexao = (src_addr, src_port, dst_addr, dst_port)

        if (flags & FLAGS_SYN) == FLAGS_SYN:
            # A flag SYN estar setada significa que é um cliente tentando estabelecer uma conexão nova
            # TODO: talvez você precise passar mais coisas para o construtor de conexão
            conexao = self.conexoes[id_conexao] = Conexao(self, id_conexao, seq_no)

            # Constroi o ack
            seq_no = conexao.seq_no
            ack_no = seq_no + 1
            header = make_header(self.porta, src_port, seq_no, ack_no, FLAGS_SYN | FLAGS_ACK)

            #Envia o ack;:
            self.rede.enviar(fix_checksum(header, src_addr, dst_addr), src_addr)
            
            if self.callback:
                self.callback(conexao)
        elif id_conexao in self.conexoes:
            # Passa para a conexão adequada se ela já estiver estabelecida
            self.conexoes[id_conexao]._rdt_rcv(seq_no, ack_no, flags, payload)
        else:
            print('%s:%d -> %s:%d (pacote associado a conexão desconhecida)' %
                  (src_addr, src_port, dst_addr, dst_port))

def redefineAddress(id_conexao):
    return id_conexao[0],id_conexao[1],id_conexao[2],id_conexao[3],
class Conexao:
    def __init__(self, servidor, id_conexao, seq_no):
        self.servidor = servidor
        self.id_conexao = id_conexao
        self.seq_no = seq_no
        self.callback = None
        self.timer = asyncio.get_event_loop().call_later(1, self._exemplo_timer)  # um timer pode ser criado assim; esta linha é só um exemplo e pode ser removida
        #self.timer.cancel()   # é possível cancelar o timer chamando esse método; esta linha é só um exemplo e pode ser removida

    def _exemplo_timer(self):
        # Esta função é só um exemplo e pode ser removida
        print('Este é um exemplo de como fazer um timer')


    def _rdt_rcv(self, seq_no, ack_no, flags, payload):
        if (seq_no != self.ack_no) and len(payload) != 0:

            return
        else :
            self.ack_no = seq_no + len(payload)

            if (len(payload) != 0) or (flags & FLAGS_SYN) or (flags & FLAGS_FIN):
                dst_address, src_port, src_address, dst_port = redefineAddress(self.id_conexao)
                header = make_header(dst_port, src_port, self.seq_no, self.ack_no, FLAGS_ACK)
                self.servidor.rede.enviar(fix_checksum(header, src_address, dst_address), src_address)

            self.callback(self, payload)


        print('recebido payload: %r' % payload)

    # Os métodos abaixo fazem parte da API

    def registrar_recebedor(self, callback):
        """
        Usado pela camada de aplicação para registrar uma função para ser chamada
        sempre que dados forem corretamente recebidos
        """
        self.callback = callback

    def enviar(self, dados):
        """
        Usado pela camada de aplicação para enviar dados
        """
        src_port, dst_port, seq_no, ack_no, flags, window_size, checksum, urg_ptr = read_header(dados)

        if (flags& FLAGS_ACK == FLAGS_ACK):
            return
        
        data_length = len(dados)
        bytes_sent = 0
        
        dst_address, src_port, src_address, dst_port = redefineAddress(self.id_conexao)

        if (bytes_sent < data_length) :
            while (bytes_sent < data_length) :
                segment_size = min(MSS, data_length - bytes_sent)
                segment_data = dados[bytes_sent: bytes_sent + segment_size]
                header = make_header(dst_port, src_port, self.seq_no + 1, self.ack_no, FLAGS_ACK)
                self.servidor.rede.enviar(fix_checksum(header + segment_data + src_address, dst_address), dst_address)

                self.seq_no = self.seq_no + segment_size
                bytes_sent += segment_size


        pass

    def fechar(self):
        """
        Usado pela camada de aplicação para fechar a conexão
        """
    
        dst_address, src_port, src_address, dst_port = redefineAddress(self.id_conexao)
        header = make_header(dst_port, src_port, self.seq_no + 1, self.ack_no, FLAGS_FIN)
        self.servidor.rede.enviar(fix_checksum(header, src_address, dst_address), src_address)

        pass


