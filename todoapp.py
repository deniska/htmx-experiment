import h
import bottle
from sqlalchemy import create_engine, String, select, delete
from sqlalchemy.orm import sessionmaker, DeclarativeBase, mapped_column, Mapped
from alcbottle import AlcBottle

engine = create_engine('sqlite:///bigdata.dat')
Session = sessionmaker(engine)

class Base(DeclarativeBase):
    pass

class Item(Base):
    __tablename__ = 'item'
    id: Mapped[int] = mapped_column(primary_key = True)
    name: Mapped[str]
    done: Mapped[bool]

    def view(self):
        return h.div(
            {'class': ['item', *iif(self.done, ['checked'])]},
            h.label(
                h.input({
                    'name': 'checked',
                    'type': 'checkbox',
                    **iif(self.done, {'checked': ''}),
                    'hx-post': f'/todo/{self.id}/set',
                    'hx-swap': 'outerHTML',
                    'hx-target': 'closest .item',
                }),
                self.name,
            ),
            h.button(
                {'hx-get': f'/todo/{self.id}/edit', 'hx-target': 'closest .item', 'hx-swap': 'outerHTML'},
                'Изменить'
            ),
            h.button(
                {'hx-delete': f'/todo/{self.id}', 'hx-swap': 'delete', 'hx-target': 'closest .item'},
                'Удалить',
            ),
        )

    def edit_view(self):
        return h.div(
            {'class': ['item', *iif(self.done, ['checked'])]},
            h.form(
                h.input({'name': 'todo', 'id': 'todoinput', 'autocomplete': 'off', 'value': self.name}),
                h.button(
                    {'hx-post': f'/todo/{self.id}/edit', 'hx-target': 'closest .item', 'hx-swap': 'outerHTML'},
                    'Сохранить',
                ),
            )
        )

app = bottle.Bottle()
app.install(AlcBottle(Session))
app.install(h.HBo())

@app.get('/')
def index(session):
    items = session.scalars(select(Item).order_by(Item.id))
    return h.html(
        h.head(h.title('ToDo App'), h.style(css)),
        h.body(
            h.script({'src': 'https://unpkg.com/htmx.org@2.0.4'}),
            h.div(
                {'class': 'content'},
                h.h1('Тудушки'),
                h.div(
                    {'class': 'todos'},
                    *(item.view() for item in items),
                ),
                h.form(
                    h.input({'name': 'todo', 'id': 'todoinput', 'autocomplete': 'off'}),
                    h.button(
                        {
                            'hx-post': '/todo',
                            'hx-target': '.todos',
                            'hx-swap': 'beforeend',
                            'hx-on::after-request': "todoinput.value=''",
                        },
                        'Добавить',
                    ),
                ),
            ),
        ),
    )

@app.post('/todo')
def post_todo(session):
    todo = Item(name = bottle.request.forms.todo, done=False)
    session.add(todo)
    session.commit()
    return todo.view()

@app.delete('/todo/<id:int>')
def delete_todo(id, session):
    session.execute(delete(Item).where(Item.id==id))
    session.commit()

@app.post('/todo/<id:int>/set')
def set_todo(id, session):
    item = session.scalar(select(Item).where(Item.id == id))
    item.done = bool(bottle.request.forms.checked)
    session.commit()
    return item.view()

@app.post('/todo/<id:int>/edit')
def post_edit_todo(id, session):
    item = session.scalar(select(Item).where(Item.id == id))
    item.name = bottle.request.forms.todo
    session.commit()
    return item.view()

@app.get('/todo/<id:int>/edit')
def get_edit_todo(id, session):
    item = session.scalar(select(Item).where(Item.id == id))
    return item.edit_view()

def iif(v, q):
    if v:
        return q
    return type(q)()

css = '''
body {
    font-family: sans-serif;
    background: #edede9;
}
.content {
    background: #f5ebe0;
    width: 400px;
}
.item {
    background: #d5bdaf;
    margin: 5px;
}
.item.checked {
    background: #e3d5ca;
}
.item button {
    margin: 5px;
}
.item label {
    display: inline-block;
    width: 55%;
}
form input {
    margin: 5px;
    width: 70%;
}
'''

if __name__ == '__main__':
    Base.metadata.create_all(engine)
    app.run(port=1234, reload=True)
