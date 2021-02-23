import torch.nn as nn
from ink.nn.layers.bilstm import BILSTM
from ink.nn.layers.bert import Bert_Encoder
from ink.nn.layers.mlp import MultiDecoder
from ink.nn.layers.crf import CRF


def batchify_with_label(inputs, outputs=None):
    # batch_size * seq_len * num_classes
    resize_inputs = inputs[:, :outputs.size(1)]
    return resize_inputs


class BERT_LSTM(nn.Module):
    def __init__(self, input_size, hidden_size, label_sizes, toplayer='CRF', bert_route='bert-base-chinese'):
        super().__init__()

        self.bert_encoder = Bert_Encoder()
        # also input dim of LSTM
        self.bert_out_dim = self.bert_encoder.out_dim
        # LSTM layer
        self.lstm = BILSTM(input_size=self.bert_out_dim,
                           hidden_size=hidden_size)

        if toplayer == 'CRF':
            self.uplayer = CRF(label_sizes)
            self.decoder = MultiDecoder(hidden_size * 2, label_sizes, True)
        else:
            self.uplayer = lambda logits, mask=None, task=None: (0, logits.argmax(dim=-1))
            self.decoder = MultiDecoder(hidden_size * 2, label_sizes, False)

    def predict(self, task, sent, mask):
        # sent,tags,masks: (batch * seq_length)
        bert_out = self.bert_encoder(sent, mask)[0]
        # bert_out: (batch * seq_length * bert_hidden = 768)
        feats = self.lstm(bert_out, mask)[0]
        logits = self.decoder(feats, task)
        mask = batchify_with_label(mask, logits)
        _, out = self.uplayer(logits, mask, task)
        return out

    def set_device(self, device):
        self.bert_encoder = self.bert_encoder.to(device)
        self.lstm = self.lstm.to(device)
        self.decoder.set_device(device)
        self.uplayer.set_device(device)