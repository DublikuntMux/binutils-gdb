.set noreorder
.text
# lvi accepts decimal binary32 values or explicit hexadecimal raw bits.
# Vector brackets contain lanes in row/column order, including offset starts.
lvi.s S733,3.14
lvi.s S000,0x7fc12345
lvi.s S001,-0x80000000
lvi.q C010,[0x00000000,0x00001234,0xffff8000,0xffffffff]
lvi.p C712,[1.0,-2.5]
lvi.p R721,[3.14,-0.0]
lvi.t C731,[1.0,2.0,3.0]
lvi.t R713,[-1.0,-2.0,-3.0]
lvi.q C700,[1.0,2.0,3.0,4.0]
lvi.q R703,[4.0,3.0,2.0,1.0]
# lvhi packs consecutive IEEE binary16 values low half first, two per scalar.
lvhi.s S123,[-0.0,0.000000059604644775390625]
lvhi.p C702,[1.0,-2.0,65504.0,0.000000059604644775390625]
lvhi.p R720,[1.00048828125,1.0005,-0.0,-65504.0]
