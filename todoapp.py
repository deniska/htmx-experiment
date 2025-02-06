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

def item_view(item):
    return h.div(
        {'class': ['item', *iif(item.done, ['checked'])]},
        h.label(
            h.input({
                'name': 'checked',
                'type': 'checkbox',
                **iif(item.done, {'checked': ''}),
                'hx-post': f'/todo/{item.id}/set',
                'hx-swap': 'outerHTML',
                'hx-target': 'closest .item',
            }),
            item.name,
        ),
        h.button(
            {'hx-get': f'/todo/{item.id}/edit', 'hx-target': 'closest .item', 'hx-swap': 'outerHTML'},
            'Edit'
        ),
        h.button(
            {'hx-delete': f'/todo/{item.id}', 'hx-swap': 'delete', 'hx-target': 'closest .item'},
            'Delete',
        ),
    )

def item_edit_view(item):
    return h.div(
        {'class': ['item', *iif(item.done, ['checked'])]},
        h.form(
            h.input({'name': 'todo', 'autocomplete': 'off', 'value': item.name}),
            h.button(
                {'hx-post': f'/todo/{item.id}/edit', 'hx-target': 'closest .item', 'hx-swap': 'outerHTML'},
                'Save',
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
                h.h1('Todo'),
                h.div(
                    {'class': 'todos'},
                    *(item_view(item) for item in items),
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
                        'Add',
                    ),
                ),
            ),
        ),
    )

@app.post('/todo')
def post_todo(session):
    item = Item(name = bottle.request.forms.todo, done=False)
    session.add(item)
    session.commit()
    return item_view(item)

@app.delete('/todo/<id:int>')
def delete_todo(id, session):
    session.execute(delete(Item).where(Item.id==id))
    session.commit()

@app.post('/todo/<id:int>/set')
def set_todo(id, session):
    item = session.scalar(select(Item).where(Item.id == id))
    item.done = bool(bottle.request.forms.checked)
    session.commit()
    return item_view(item)

@app.post('/todo/<id:int>/edit')
def post_edit_todo(id, session):
    item = session.scalar(select(Item).where(Item.id == id))
    item.name = bottle.request.forms.todo
    session.commit()
    return item_view(item)

@app.get('/todo/<id:int>/edit')
def get_edit_todo(id, session):
    item = session.scalar(select(Item).where(Item.id == id))
    return item_edit_view(item)

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
    display: flex;
    align-items: center;
}
.item.checked {
    background: #e3d5ca;
}
.item button {
    margin: 5px;
}
.item label {
    display: inline-block;
    flex-grow: 1;
}
.content form {
    width: 100%;
    display: flex;
    align-items: center;
}
form input {
    margin: 5px;
    flex-grow: 1;
}
'''

if __name__ == '__main__':
    Base.metadata.create_all(engine)
    app.run(port=1234, debug=True, reloader=True)
