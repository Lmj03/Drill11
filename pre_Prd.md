AutoRun 상태 추가

main.py grass.py boy.py

grass는 grass.png를 이용한 이미지 출력에 관한 py.

boy.py는 boy class에 관한 내용으로 상태머신에 따른 boy의 행동 양상이 달라짐.

main.py는 grass.py와 boy.py를 import하여 각각의 파이썬 파일에서 함수를 꺼내와 게임 로직을 진행하는 파이썬 파일

boy.py는 boy의 클래스가 작성되어있어야함.

boy는 처음 진입시 IDLE상태.
a키를 누르면 소년은 자동 무적 런(AUTO RUN) 상태가 되어 키조작 없어도 계속 좌우로 이동해야함. 또한 AUTO RUN상태에서는 소년의 속도가 점점 빨라지며 크기가 점점 커져야함. AUTORUN 상태 5초 지속되면 IDLE상태로 돌아가거나 방향키가 눌려지면 눌린 방향으로 움직이는 원래의 run 상태로 돌아옴. AUTO RUN모드에서 커진 속도와 크기는 모드 해제시 원래의 속도와 크기로 돌아와야함. 

pico2d를 이용할 것. 커밋 20개 기록을 남겨야 할 것.
