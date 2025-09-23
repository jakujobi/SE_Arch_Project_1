---

---

---

---

---

---

**Initial Software Architecture Research Project Proposal**

**Draix** Wyatt, John Akujobi, Jevic Kapuku, Kale Nelson** **

**McComish** Department of Electrical Engineering and Computer Science** **

**Mr. Ken Gamradt**

**SE 340:  Software Architecture**

**September 10, 2025**

**First Choice: Decorator Pattern**

**Topic: Role-based news app with layered implementation**

**Problem: We need to create a maintainable news site that allows for different tiers of subscribers to access **different types** and degrees of content that accesses content and uses APIs under a single implementation.**

**Context: The website will include a free tier that only allows viewing of headlines, a standard tier that allows access to a limited selection of articles, and a premium tier that allows access to all available features. This website will be implemented in Django with PostgreSQL as the database. Content will be fetched from news APIs such as NewsData.io and News API.**

**Solution: We will create several underlying classes as base classes. One such class will implement our API fetching functionality. Another will implement a content management system layered over the API class. Finally, a display class will display the **appropriate content** to the user on top of the content management class.**

**Second Choice: Factory Method Pattern**

**Dynamic content posting website: Users will post content to a website; however, knowing which class to instantiate (blog, news, opinion, comments) is non-intuitive. We will create an abstract content class and have concrete classes of each type, with a control class that will decide which to instantiate.**

**Third Choice: Adapter Pattern**

**API call adapter: In website development, we rely on APIs with specific argument types. These types **may** with how the website is developed; we can create adapter classes to make the API implementation easier.**
