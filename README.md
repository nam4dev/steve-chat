The code works, but it is not very clean to me.

  - You should organize it well. Separate the different layers.
  - You need to add a script to initialize your database (MySQL or SQLite3).
  - You need to add a requirements.txt file with needed Pip packages and versions at the root of your project to ease setup.
  - You need to follow the tutorial link I put in the code to configure MySQL if you really need to (https://hevodata.com/learn/flask-mysql/).
  - You need to update the SQLite3 database path as it uses my file system to make it work.

**As an advice, you should use a development configuration with SQLite3 and a production one with MySQL**

Good luck!
