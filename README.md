## fork of fnf-to-sm that uses singles and also has more functionality maybe
# READ THIS, if you try to use it blindly the program probably will shit itself and die or idk

here's the bare minimum you need to know

the basic usage is just passing the .sm in question as an argument; it then shits out a json

![image](https://user-images.githubusercontent.com/53107421/142876194-2d5f8f0b-02d0-408a-b765-8c957645222a.png)

the .sm needs to be formatted in a very specific way though, because arrowvortex's dance double editing sucks prolapsed placenta so to get around that, it instead uses 3 charts. (also this makes it way easier to playtest in etterna)

![image](https://user-images.githubusercontent.com/53107421/142876686-ca1e0fd9-39b5-4d9a-91f2-04874db30f3f.png)

1. **Medium**: used for indicating mustHitSection, AKA: _whether the camera focuses on bf or not._
if there is _**one**_ mine at the start of a measure (those big lines with numbers) it will focus the camera on bf for
that section
2. **Hard**: enemy's side
3. **Challenge**: bf's side

DUE TO SOME SHITTY WORKAROUNDS if bf's side has more sections than the enemy's side (e.g. bf sings until sect 49 and enemy until 47) the program does some weird shit to those last 2 sections, to prevent this, _put a mine on the last enemy section where bf sings_
(in the example i just gave, bf stops singing at 49 so you put a mine on 48 in the Hard chart)

![image](https://user-images.githubusercontent.com/53107421/142878887-2b05e7fc-ca08-4f18-84a5-98e6617598e6.png)

1. The .sm's Title is the song name/filename the converter will spit out.
2. The Artist is the stage
3. The program automatically tries to detect difficulty. if the path has "\_ez" it detects easy, "\_n" normal, if it has neither it defaults to hard

![image](https://user-images.githubusercontent.com/53107421/142882977-603067c5-f107-4f0f-a876-c27b91177871.png)



**To change the singers and scroll speeds** you have to edit the .py itself

![image](https://user-images.githubusercontent.com/53107421/142879590-ebfc5a05-e519-4875-a11c-6f3f630f2110.png)

i put some default scroll speeds i think are fit for each difficulty; there's probably a way to implement these arguments as something you pass into the program but my knowledge of python is neanderthal

with this knowledge you may be able to use this without it crumbling like a termite-infested studio apartment
