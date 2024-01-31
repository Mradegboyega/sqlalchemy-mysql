from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Annotated
from sqlalchemy import exc
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

class ChoiceBase(BaseModel):
    choice_text: str
    is_correct: bool

class ChoiceResponse(BaseModel):
    id: int
    choice_text: str
    is_correct: bool

class QuestionBase(BaseModel):
    question_text: str
    choices: List[ChoiceBase]

class QuestionResponse(BaseModel):
    id: int
    question_text: str
    choices: List[ChoiceResponse]

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@app.post("/questions/", response_model=QuestionResponse)
async def create_question(question: QuestionBase, db: db_dependency):
    try:
        db_question = models.Question(question_text=question.question_text)
        db.add(db_question)
        db.flush()
        db.refresh(db_question)

        for choice in question.choices:
            db_choice = models.Choices(
                choice_text=choice.choice_text,
                is_correct=choice.is_correct,
                question_id=db_question.id
            )
            db.add(db_choice)
        
        db.flush()

        # Update the choices attribute in db_question
        db_question.choices = db.query(models.Choices).filter(models.Choices.question_id == db_question.id).all()

        db.commit()
        
        # You can also return the created question with its choices
        return QuestionResponse(
            id=db_question.id,
            question_text=db_question.question_text,
            choices=[
                ChoiceResponse(id=choice.id, choice_text=choice.choice_text, is_correct=choice.is_correct)
                for choice in db_question.choices
            ]
        )
    except exc.SQLAlchemyError as e:
        db.rollback()
        print(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    

@app.get("/questions/{question_id}", response_model=QuestionResponse)
async def read_question(question_id: int, db: db_dependency):
    result = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Question not found")
    return result

@app.get("/choices/{question_id}", response_model=List[ChoiceResponse])
async def read_choices(question_id: int, db: db_dependency):
    results = db.query(models.Choices).filter(models.Choices.question_id == question_id).all()
    if not results:
        raise HTTPException(status_code=404, detail="Choices not found")
    return results
