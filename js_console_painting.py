import cv2
import numpy as np

from math import ceil

img = 'hina2.jpg'
shape = (200, 220)
# shape = (130, 200)

origin_img = img = cv2.cvtColor(cv2.imread(img), cv2.COLOR_BGR2RGB)

while img.shape[0] >= shape[0] or img.shape[1] >= shape[1]:
    dstsize = (img.shape[1] // 2, img.shape[0] // 2)
    print(f'img.shape: {img.shape}, dstsize: {dstsize}')
    img = cv2.pyrDown(img, dstsize=dstsize)
   
print(f'img.shape: {img.shape}')

# if img.shape[0] > shape[0] or img.shape[1] > shape[1]:
#     rate = min(shape[0] / img.shape[0], shape[1] / img.shape[1])
#     print(f'rate: {rate}, dstsize: {ceil(img.shape[1]*rate)}, {ceil(img.shape[0]*rate)}')
#     img = cv2.pyrDown(img, dstsize=(ceil(img.shape[1]*rate), ceil(img.shape[0]*rate)))

print(f'img.shape: {img.shape}')

ls = np.zeros(img.shape[:2], dtype='object')

for r in range(img.shape[0]):
    for c in range(img.shape[1]):
        ls[r][c] = '{:X}{:X}{:X}'.format(*img[r][c])

with open('a.html', encoding='utf8', mode='w') as f:
    f.write(f'<html><script>const shape=[{img.shape[0]}, {img.shape[1]}]; const arr=')
    f.write(str(ls.tolist()))
    f.write(''';
let r = 0;
let handle = setInterval(() => {
    if (r < shape[0]) {
        let str = ''
        let s = []
        for (let c = 0; c < shape[1]; c++) {
            str += '%c    ';
            s.push('background: #' + arr[r][c] + '; margin: 0px; padding: 0px;');
        }
        console.log(str, ...s);
        r++;
    } else 
        clearInterval(handle);
}, 100)
</script>

</html>''')