# Copyright 2021 Google LLC
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import tensorflow_datasets as tfds
import tensorflow as tf
import os
import struct
import numpy as np
from transformers import GPT2Tokenizer
import multiprocessing as mp

import argparse

parser = argparse.ArgumentParser(description='Load a dataset.')
parser.add_argument('--data_dir', type=str)
parser.add_argument('--save_dir', type=str)
parser.add_argument('--name', type=str)
parser.add_argument('--split', type=str)
parser.add_argument('--tokenize', action='store_true')

args = parser.parse_args()

if args.tokenize:
    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")

split = args.split
data_dir = args.data_dir
save_dir = args.save_dir
dataset_name = args.name


ds = tfds.load(dataset_name, split=split, shuffle_files=False, batch_size=2**16,
               data_dir=data_dir)
assert isinstance(ds, tf.data.Dataset)
print(ds)

UID = 0
def sep():
    global UID
    UID += 1
    return b"\xff\xff"+struct.pack("<I", UID)

def tok(x):
    if args.tokenize:
        out = tokenizer.encode(x.decode("utf8"))
        out = np.array(out, dtype=np.uint16).view(np.uint8).tobytes()
    else:
        out = x
    return out


fout = open(os.path.join(save_dir, dataset_name+"."+split), "wb")

p = mp.Pool(96)

i = 0
sizes = [0]
for b in ds:
    print(i)

    text = b['text'].numpy()
    text = p.map(tok,text)
    
    for x in text:
        next_line = sep()+x
        fout.write(next_line)
        sizes.append(sizes[-1]+len(next_line))
    i += 1

open(os.path.join(save_dir,dataset_name+"."+split+".size"), "wb").write(np.array(sizes,dtype=np.uint64).tobytes())
